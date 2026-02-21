# services/email_analyzer.py — Reads Gmail metadata and analyzes it
# IMPORTANT: We only read metadata (size, date, labels) — never the email body/content

from datetime import datetime, timezone, timedelta
from googleapiclient.http import BatchHttpRequest

# How old an email must be (in days) to be considered "old"
OLD_EMAIL_THRESHOLD_DAYS = 365

# Size (in bytes) above which an email is considered to have a "large attachment"
# 1 MB = 1,048,576 bytes
LARGE_ATTACHMENT_THRESHOLD_BYTES = 1_048_576  # 1 MB

# Max emails to analyze — Gmail API returns up to 500 per page
# For a full account scan, you'd paginate (loop through pages), but 500 is good for demo
MAX_EMAILS_TO_FETCH = 500


def analyze_emails(service):
    """
    Fetches Gmail message metadata and returns analysis stats using batching.
    """
    try:
        # --- Step 1: Get a list of all message IDs ---
        print("Fetching message IDs...")
        results = service.users().messages().list(
            userId="me",           # "me" = the authenticated user
            maxResults=MAX_EMAILS_TO_FETCH
        ).execute()

        messages = results.get("messages", [])

        if not messages:
            return {
                "total_emails": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0,
                "old_emails_count": 0,
                "large_attachment_emails_count": 0,
                "analyzed_count": 0
            }, None

        # --- Step 2: Fetch metadata for each message in BATCHES ---
        print(f"Got {len(messages)} messages. Starting batch fetch...")
        
        # State to track across callbacks
        stats = {
            "total_size_bytes": 0,
            "old_emails_count": 0,
            "large_attachment_count": 0
        }
        
        one_year_ago = datetime.now(timezone.utc) - timedelta(days=OLD_EMAIL_THRESHOLD_DAYS)
        
        # Callback for the batch request
        def process_message(request_id, response, exception):
            if exception is not None:
                print(f"⚠️ Error fetching msg {request_id}: {exception}")
                return
            
            try:
                # --- Size analysis ---
                size = response.get("sizeEstimate", 0)
                stats["total_size_bytes"] += size

                if size >= LARGE_ATTACHMENT_THRESHOLD_BYTES:
                    stats["large_attachment_count"] += 1

                # --- Age analysis ---
                internal_date_ms = int(response.get("internalDate", 0))
                email_date = datetime.fromtimestamp(
                    internal_date_ms / 1000,
                    tz=timezone.utc
                )

                if email_date < one_year_ago:
                    stats["old_emails_count"] += 1
            except Exception as e:
                print(f"⚠️ Error processing msg {request_id}: {e}")

        # Gmail API allows up to 100 requests per batch
        BATCH_SIZE = 100
        
        for i in range(0, len(messages), BATCH_SIZE):
            batch = service.new_batch_http_request()
            batch_messages = messages[i:i + BATCH_SIZE]
            
            for msg in batch_messages:
                # Add each request to the batch using the message ID as the request ID for tracking later
                req = service.users().messages().get(
                    userId="me",
                    id=msg["id"],
                    format="metadata",
                    metadataHeaders=[]
                )
                batch.add(req, callback=process_message, request_id=msg["id"])
                
            print(f"Executing batch {i // BATCH_SIZE + 1} ({len(batch_messages)} messages)...")
            batch.execute()

        # --- Step 3: Get total mailbox storage from Gmail profile ---
        print("Fetching profile stats...")
        profile = service.users().getProfile(userId="me").execute()
        total_messages_in_account = profile.get("messagesTotal", len(messages))

        # Convert bytes to MB for easier reading
        total_size_mb = round(stats["total_size_bytes"] / (1024 * 1024), 2)

        return {
            "total_emails_in_account": total_messages_in_account,
            "emails_analyzed": len(messages),
            "total_size_bytes": stats["total_size_bytes"],
            "total_size_mb": total_size_mb,
            "old_emails_count": stats["old_emails_count"],           # Emails older than 1 year
            "large_attachment_emails_count": stats["large_attachment_count"],  # Emails > 1MB
            "old_email_percentage": round(
                (stats["old_emails_count"] / len(messages)) * 100, 1
            ) if messages else 0,
            "analysis_limit": MAX_EMAILS_TO_FETCH,
            "note": f"Analyzed {len(messages)} most recent emails. Your account has {total_messages_in_account} total."
        }, None

    except Exception as e:
        return None, f"Failed to analyze emails: {str(e)}"

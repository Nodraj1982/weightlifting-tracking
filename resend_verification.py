from supabase import create_client

# Your Supabase project URL and service role key (⚠️ keep this secret!)
SUPABASE_URL = "https://snltqtknffxtqhqcqbgg.supabase.co"
SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNubHRxdGtuZmZ4dHFocWNxYmdnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1OTAwNTIzOSwiZXhwIjoyMDc0NTgxMjM5fQ.SvRjrL-NygfGb6Tm79Xqelo_Isk8u-tAomY4VrRKEik"

supabase = create_client(SUPABASE_URL, SERVICE_ROLE_KEY)

# Replace with your wife's email
email = "sian.burns@googlemail.com"

# Resend the verification email
response = supabase.auth.admin.resend_confirmation_email(email)
print(response)
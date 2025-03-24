from supabase import create_client

SUPABASE_URL = "https://oaacsxbwcdnpncxswxsx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9hYWNzeGJ3Y2RucG5jeHN3eHN4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDI4Mjc5NDgsImV4cCI6MjA1ODQwMzk0OH0.pLVwF75onyhNeDtlCvvKH7OSh8AFiT4cE5XNGOvqOdE"

def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

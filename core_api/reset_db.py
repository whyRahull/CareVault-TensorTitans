import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carevault_core.settings')
django.setup()

def drop_all_tables():
    with connection.cursor() as cursor:
        cursor.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO public;")
        print("Dropped and recreated 'public' schema.")

if __name__ == "__main__":
    drop_all_tables()

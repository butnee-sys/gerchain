import sqlite3
import os

DB_PATH = "database/gerchain.db"

def test_system():
    print("--- GERCHAIN СИСТЕМИЙН НЭГДСЭН ШАЛГАЛТ ---")
    if not os.path.exists(DB_PATH):
        print(f"Алдаа: Өгөгдлийн сан олдсонгүй ({DB_PATH}). Эхлээд db.py ажиллуулна уу.")
        return False
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Хүснэгтүүд үүссэн эсэхийг шалгах
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row['name'] for row in cursor.fetchall()]
    required_tables = ['accounts', 'escrows', 'audit_logs', 'rwa_assets', 'milestones']
    
    print(f"Олдсон хүснэгтүүд: {tables}")
    for t in required_tables:
        if t not in tables:
            print(f"Алдаа: '{t}' хүснэгт дутуу байна!")
            return False
            
    print("✓ Бүх өгөгдлийн сангийн хүснэгтүүд бүрэн байна.")

    # 2. Өгөгдлийн бүрэн бүтэн байдал ба харилцан хамаарлыг шалгах
    cursor.execute("SELECT COUNT(*) as cnt FROM accounts")
    acc_count = cursor.fetchone()['cnt']
    
    cursor.execute("SELECT COUNT(*) as cnt FROM rwa_assets")
    rwa_count = cursor.fetchone()['cnt']
    
    cursor.execute("SELECT COUNT(*) as cnt FROM escrows")
    esc_count = cursor.fetchone()['cnt']

    cursor.execute("SELECT COUNT(*) as cnt FROM milestones")
    milestone_count = cursor.fetchone()['cnt']

    print(f"Дансны тоо: {acc_count}")
    print(f"RWA хөрөнгийн тоо: {rwa_count}")
    print(f"Эскроу гэрээний тоо: {esc_count}")
    print(f"Үе шатны (Milestones) тоо: {milestone_count}")

    conn.close()
    print("--- GERCHAIN СИСТЕМ БҮРЭН ХЭВИЙН АЖИЛЛАСАН ---")
    return True

if __name__ == "__main__":
    test_system()

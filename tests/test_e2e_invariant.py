import sqlite3
import os
import sys
import hashlib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

DB_PATH = "database/gerchain.db"

def run_e2e_invariant_test():
    print("--- GERCHAIN E2E INVARIANT & STATE TEST START ---")
    
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    from database.db import init_db, log_transition
    init_db()
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO accounts (wallet_address, owner_name, balance) VALUES (?, ?, ?)", 
                       ("wallet_sender", "Бат (Илгээгч)", 10000.0))
        cursor.execute("INSERT INTO accounts (wallet_address, owner_name, balance) VALUES (?, ?, ?)", 
                       ("wallet_receiver", "Дорж (Хүлээн авагч)", 2000.0))
        conn.commit()
        
        cursor.execute("SELECT SUM(balance + locked_balance) as total FROM accounts")
        total_initial = cursor.fetchone()['total']
        assert total_initial == 12000.0, f"АЛДАА: Балансын хууль зөрчигдлөө! Нийт дүн: {total_initial}"
        print("✓ [CREATE] Дансны эхлэх балансын инвариант шалгагдлаа (12000 NEF).")

        escrow_id = "ESC-2026-001"
        amount = 3000.0
        cursor.execute("INSERT INTO escrows (id, sender_address, receiver_address, amount, state, condition_desc) VALUES (?, ?, ?, ?, 'CREATED', ?)", 
                       (escrow_id, "wallet_sender", "wallet_receiver", amount, "Мод тарих төслийн урьдчилгаа"))
        conn.commit()
        log_transition(escrow_id, "NONE", "CREATED", "admin")

        cursor.execute("UPDATE accounts SET balance = balance - ?, locked_balance = locked_balance + ? WHERE wallet_address = ?", 
                       (amount, amount, "wallet_sender"))
        cursor.execute("UPDATE escrows SET state = 'LOCKED' WHERE id = ?", (escrow_id,))
        conn.commit()
        log_transition(escrow_id, "CREATED", "LOCKED", "admin")

        cursor.execute("SELECT SUM(balance + locked_balance) as total FROM accounts")
        total_locked_state = cursor.fetchone()['total']
        assert total_locked_state == 12000.0, "АЛДАА: LOCK хийх үед мөнгө үрэгдсэн эсвэл нэмэгдсэн!"
        
        cursor.execute("SELECT balance, locked_balance FROM accounts WHERE wallet_address = 'wallet_sender'")
        sender = cursor.fetchone()
        assert sender['balance'] == 7000.0 and sender['locked_balance'] == 3000.0, "АЛДАА: Илгээгчийн баланс буруу байна!"
        print("✓ [LOCK] Түгжих үеийн балансын инвариант амжилттай шалгагдлаа.")

        cursor.execute("UPDATE accounts SET locked_balance = locked_balance - ? WHERE wallet_address = ?", (amount, "wallet_sender"))
        cursor.execute("UPDATE accounts SET balance = balance + ? WHERE wallet_address = ?", (amount, "wallet_receiver"))
        cursor.execute("UPDATE escrows SET state = 'RELEASED' WHERE id = ?", (escrow_id,))
        conn.commit()
        log_transition(escrow_id, "LOCKED", "RELEASED", "admin")

        cursor.execute("SELECT SUM(balance + locked_balance) as total FROM accounts")
        total_final = cursor.fetchone()['total']
        assert total_final == 12000.0, "АЛДАА: RELEASE хийх үед нийт баланс өөрчлөгдлөө!"

        cursor.execute("SELECT balance FROM accounts WHERE wallet_address = 'wallet_receiver'")
        receiver = cursor.fetchone()
        assert receiver['balance'] == 5000.0, "АЛДАА: Хүлээн авагчийн мөнгө буруу орсон байна!"
        print("✓ [RELEASE] Чөлөөлөх үеийн санхүүгийн инвариант бүрэн хангагдлаа.")

        # Аудитын лог шалгах (Нийт 3 төлөв шилжилт үүссэн байх ёстой)
        cursor.execute("SELECT * FROM audit_logs WHERE escrow_id = ?", (escrow_id,))
        logs = cursor.fetchall()
        assert len(logs) == 3, f"АЛДАА: Аудитын лог дутуу эсвэл илүү байна. (Олдсон: {len(logs)})"
        
        for log in logs:
            raw = f"{log['escrow_id']}:{log['previous_state']}:{log['new_state']}:{log['actor']}:{log['timestamp']}"
            expected_hash = hashlib.sha256(raw.encode('utf-8')).hexdigest()
            assert log['tx_hash'] == expected_hash, f"КРИПТОГРАФИК АЛДАА: tx_hash зөрүүтэй байна!"
        print("✓ [AUDIT] SHA-256 криптографик аудитын мөрийн бүрэн бүтэн байдал баталгаажлаа.")

        print("\n--- БҮХ E2E INVARIANT ТЕСТ АМЖИЛТТАЙ ДУУСЛАА ---")
        return True

    except AssertionError as e:
        print(f"\n❌ ТЕСТ АЛДАА ГАРЛАА: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    run_e2e_invariant_test()

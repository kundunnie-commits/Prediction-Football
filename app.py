import streamlit as tf
import pandas as pd
import sqlite3
from datetime import datetime

# ตั้งค่าหน้าเว็บแอปพลิเคชัน
tf.set_page_config(page_title="World Cup 2026 Quant System V2", page_icon="📊", layout="wide")

# โครงสร้างตารางค่าน้ำ (Payout Matrix) ที่ถอดรหัสจากเจ้ามือ
# รูปแบบ: { "ค่าน้ำ": {"ต่อ": อัตราจ่าย, "รอง": อัตราจ่าย} }
PAYOUT_MATRIX = {
    "+10": {"ต่อ": 0.727, "รอง": 1.00},
    "ขาว": {"ต่อ": 0.80, "รอง": 1.00},
    "-10": {"ต่อ": 0.90, "รอง": 0.90},
    "-5":  {"ต่อ": 1.00, "รอง": 0.80}
}

def init_db():
    conn = sqlite3.connect('quant_football.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_recorded TEXT,
            team_fav TEXT,
            hdp_price REAL,
            hdp_water TEXT,
            ou_price REAL,
            ou_water TEXT,
            prediction TEXT,
            confidence TEXT,
            ft_score TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# หัวข้อหลักของเว็บแอป
tf.title("📊 World Cup 2026 Quant Prediction (V2.0)")
tf.markdown("### ⚙️ *Powered by Exact Payout Matrix Algorithm*")
tf.markdown("---")

tab1, tab2 = tf.tabs(["🔮 วิเคราะห์ราคา & คำนวณผลตอบแทน", "🗄️ ฐานข้อมูลสถิติ (Database)"])

with tab1:
    tf.header("🚀 ป้อนข้อมูลราคาเพื่อสแกนและหา Value Bet")
    
    col1, col2 = tf.columns(2)
    
    with col1:
        team_fav = tf.text_input("⚽ ชื่อทีมต่อ / เจ้าบ้าน", placeholder="เช่น สเปน")
        hdp_price = tf.selectbox("📐 ราคาต่อรอง แฮนดิแคป (HDP)", [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5])
        hdp_water = tf.selectbox("💧 ค่าน้ำ แฮนดิแคป", ["ขาว", "-10", "-5", "+10"])
        
    with col2:
        ou_price = tf.selectbox("🎯 ราคาสกอร์รวม (Over/Under)", [1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 3.25, 3.5, 3.75, 4.0])
        ou_water = tf.selectbox("💧 ค่าน้ำ สกอร์รวม", ["ขาว", "-10", "-5", "+10"])

    # --- อัลกอริทึมคำนวณเชิงปริมาณ (Quant Logic V2) ---
    pred_text = "รอดูสถานการณ์ (ยังไม่เข้าเงื่อนไขทำกำไรที่ชัดเจน)"
    confidence = "0%"
    alert_type = "info"
    payout_info = ""
    
    # ดึงค่าเรตจ่ายตามน้ำที่เลือก
    payout_fav = PAYOUT_MATRIX[hdp_water]["ต่อ"]
    payout_under = PAYOUT_MATRIX[hdp_water]["รอง"]
    
    # กฎข้อที่ 1: 0.75 น้ำลบ -10 (The 1-Goal Trap)
    if hdp_price == 0.75 and hdp_water == "-10":
        pred_text = f"🎯 รองทีมตรงข้าม {team_fav} (+0.75) | บ่อนล็อกเป้าชนะแค่ 1 ลูก"
        confidence = "100% (จากผล Backtest)"
        alert_type = "success"
        payout_info = f"เรตจ่ายฝั่งรอง: {payout_under:.2f} (แทง 10 ได้ {payout_under * 10:.0f})"
        
    # กฎข้อที่ 2: สกอร์รวมน้ำ -10 (Under Bias)
    elif ou_water == "-10":
        pred_text = "🎯 แทง สกอร์ต่ำ (Under) | บ่อนบีบน้ำ -10 ป้องกันหน้าต่ำ"
        confidence = "81.82%"
        alert_type = "success"
        ou_payout = PAYOUT_MATRIX["-10"]["ต่อ"] # สกอร์รวม -10 จ่าย 0.90 เท่ากัน
        payout_info = f"เรตจ่ายฝั่งต่ำ: {ou_payout:.2f} (แทง 10 ได้ {ou_payout * 10:.0f})"
        
    # กฎข้อที่ 3: สกอร์รวมน้ำขาว + ราคาไม่เกิน 2.0 (Over Bias)
    elif ou_water == "ขาว" and hdp_price < 2.0:
        pred_text = "🎯 แทง สกอร์สูง (Over) | บ่อนเปิดน้ำขาว ปล่อยเกมเปิดแลก"
        confidence = "80.00%"
        alert_type = "success"
        ou_payout = PAYOUT_MATRIX["ขาว"]["ต่อ"] # อิงการจ่ายต่ำสุดที่ 0.80
        payout_info = f"เรตจ่ายฝั่งสูง: {ou_payout:.2f} (แทง 10 ได้ {ou_payout * 10:.0f})"
        
    # กฎข้อที่ 4: ทีมใหญ่ต่อถูก ปป. (The Draw Trap)
    elif hdp_price == 0.25:
        pred_text = f"🎯 รองทีมตรงข้าม {team_fav} (+0.25) | ราคาล่อเม่า โอกาสจบเสมอสูง"
        confidence = "60.00% (เน้นกินครึ่ง ปลอดภัยสูง)"
        alert_type = "warning"
        payout_info = f"เรตจ่ายฝั่งรอง: {payout_under:.2f} (แทง 10 ได้ {payout_under * 10:.0f})"

    # --- ส่วนแสดงผลบนหน้าจอ ---
    tf.markdown("### 👁️ ผลการวิเคราะห์จากระบบ (AI Scan):")
    
    if alert_type != "info":
        full_prediction = f"{pred_text} | 💰 {payout_info}"
        if alert_type == "success":
            tf.success(f"**แผนการลงทุน:** {pred_text}\n\n**ผลตอบแทนที่คาดหวัง:** 💰 {payout_info}\n\n**Win Rate:** {confidence}")
        elif alert_type == "warning":
            tf.warning(f"**แผนการลงทุน:** {pred_text}\n\n**ผลตอบแทนที่คาดหวัง:** 💰 {payout_info}\n\n**Win Rate:** {confidence}")
    else:
        full_prediction = pred_text
        tf.info(f"**แผนการลงทุน:** {pred_text}")
        
    # แสดงโครงสร้างค่าน้ำ (ให้ผู้ใช้เห็นความลำเอียงของบ่อน)
    with tf.expander("🔍 ดูเจตนาการซ่อนค่าน้ำของบ่อนคู่นี้ (Bookie's Bias)"):
        tf.write(f"- ถ้าคนแทง **{team_fav} (ต่อ)** บ่อนจ่าย: **{payout_fav:.2f}** (แทง 10 จ่าย {payout_fav * 10:.0f})")
        tf.write(f"- ถ้าคนแทง **ทีมเยือน (รอง)** บ่อนจ่าย: **{payout_under:.2f}** (แทง 10 จ่าย {payout_under * 10:.0f})")
        if payout_fav > payout_under:
            tf.error("🚨 สัญญาณอันตราย: บ่อนยอมจ่ายฝั่งทีมต่อแพงกว่า เพื่อเป็น 'เหยื่อล่อ' ให้คนแห่แทงทีมต่อ!")
        elif payout_under > payout_fav:
            tf.info("💡 สัญญาณปกติ: บ่อนดึงน้ำฝั่งรองขึ้น เพื่อล่อให้คนเล่นรอง")

    # ปุ่มบันทึกข้อมูล
    if tf.button("💾 บันทึกคู่นี้ลงฐานข้อมูล"):
        if team_fav:
            conn = sqlite3.connect('quant_football.db')
            cursor = conn.cursor()
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            cursor.execute('''
                INSERT INTO matches (date_recorded, team_fav, hdp_price, hdp_water, ou_price, ou_water, prediction, confidence, ft_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (current_date, team_fav, hdp_price, hdp_water, ou_price, ou_water, full_prediction, confidence, "รออัปเดตผล"))
            conn.commit()
            conn.close()
            tf.balloons()
            tf.success(f"บันทึกข้อมูลคู่ {team_fav} พร้อมเรตการจ่ายเรียบร้อยแล้ว!")
        else:
            tf.error("กรุณากรอกชื่อทีมก่อนกดบันทึก")

with tab2:
    tf.header("🗄️ คลังข้อมูลประวัติศาสตร์ (World Cup 2026)")
    
    conn = sqlite3.connect('quant_football.db')
    df = pd.read_sql_query("SELECT * FROM matches ORDER BY id DESC", conn)
    conn.close()
    
    if not df.empty:
        tf.dataframe(df, use_container_width=True)
        
        tf.markdown("---")
        tf.subheader("🔄 อัปเดตสกอร์ฟุตบอล (FT Score)")
        match_id_to_update = tf.number_input("ใส่ ID แมตช์ที่เตะจบแล้ว", min_value=1, step=1)
        score_input = tf.text_input("ใส่ผลสกอร์ (เช่น 2-1)")
        
        if tf.button("✅ บันทึกสกอร์"):
            if score_input:
                conn = sqlite3.connect('quant_football.db')
                cursor = conn.cursor()
                cursor.execute("UPDATE matches SET ft_score = ? WHERE id = ?", (score_input, match_id_to_update))
                conn.commit()
                conn.close()
                tf.success(f"อัปเดตสำเร็จ! กรุณารีเฟรชหน้าเว็บ")
    else:
        tf.info("ไม่มีข้อมูลในระบบ")
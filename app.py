# -*- coding: utf-8 -*-
import logging
import pymysql
from flask import Flask, request, jsonify
from flask_cors import CORS  # CORS 추가

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})  # 모든 API 요청 허용

# ✅ 로그 설정
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

# ✅ MySQL 연결 정보 (직접 설정)
db_config = {
    'host': 'aurora-multi-master-cluster.cluster-cpyewiyugsry.ap-northeast-2.rds.amazonaws.com',  # ✅ 직접 지정
    'port': 3306,  # ✅ MySQL 기본 포트
    'user': 'cloudee',  # ✅ 직접 지정
    'password': 'jehj240424!',  # ✅ 직접 지정
    'database': 'concert',  # ✅ 직접 지정
    'cursorclass': pymysql.cursors.DictCursor
}

# ✅ MySQL 연결 함수
def get_db_connection():
    try:
        connection = pymysql.connect(**db_config)
        app.logger.info("✅ MySQL 연결 성공!")
        return connection
    except pymysql.MySQLError as e:
        app.logger.error(f"❌ MySQL 연결 실패: {str(e)}")
        return None

# ✅ 테이블 자동 생성
def create_table():
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS tickets (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                phone VARCHAR(20) NOT NULL,
                seat VARCHAR(10) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            cursor.execute(create_table_sql)
            connection.commit()
            cursor.close()
            app.logger.info("✅ 테이블 생성 완료!")
        except Exception as e:
            app.logger.error(f"❌ 테이블 생성 실패: {str(e)}")
        finally:
            connection.close()

# ✅ Health Check 엔드포인트
@app.route("/healthz", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200

# ✅ 기본 홈 엔드포인트
@app.route("/")
def home():
    return jsonify({"message": "Flask is running!"}), 200

# ✅ 좌석 예약 엔드포인트
@app.route('/api/tickets/reserve', methods=['POST', 'OPTIONS'])
def reserve_tickets():
    if request.method == "OPTIONS":
        return jsonify({"message": "Preflight request ok"}), 200

    data = request.json
    name = data.get('name')
    phone = data.get('phone')
    seats = data.get('seats')

    if not name or not phone or not seats:
        return jsonify({"message": "모든 필드를 입력하세요."}), 400

    connection = get_db_connection()
    if not connection:
        return jsonify({"message": "데이터베이스 연결 실패"}), 500

    cursor = connection.cursor()
    try:
        # 이미 예약된 좌석 확인
        query = "SELECT seat FROM tickets WHERE seat IN (%s)" % ','.join(['%s'] * len(seats))
        cursor.execute(query, seats)
        booked_seats = [row["seat"] for row in cursor.fetchall()]

        if booked_seats:
            return jsonify({"message": "이미 예약된 좌석 포함", "booked_seats": booked_seats}), 400

        # 예매 정보 삽입
        query = "INSERT INTO tickets (name, phone, seat) VALUES (%s, %s, %s)"
        for seat in seats:
            cursor.execute(query, (name, phone, seat))

        connection.commit()
        app.logger.info(f"✅ 예매 성공: {name}, {phone}, {seats}")
        return jsonify({"message": "예매 성공!", "reserved_seats": seats}), 200

    except Exception as e:
        app.logger.error(f"❌ 예매 실패: {str(e)}")
        return jsonify({"message": "예매 중 오류 발생", "error": str(e)}), 500
    finally:
        cursor.close()
        connection.close()

# ✅ 예매 내역 조회 엔드포인트
@app.route('/api/tickets', methods=['GET'])
def get_tickets():
    connection = get_db_connection()
    if not connection:
        return jsonify({"message": "데이터베이스 연결 실패"}), 500

    cursor = connection.cursor()
    try:
        cursor.execute("SELECT name, phone, seat FROM tickets")
        tickets = cursor.fetchall()
        return jsonify(tickets), 200
    except Exception as e:
        return jsonify({"message": "예매 내역 조회 중 오류 발생", "error": str(e)}), 500
    finally:
        cursor.close()
        connection.close()

# ✅ Flask 실행
if __name__ == "__main__":
    create_table()
    app.logger.info(u"Flask 서버 시작 중...")
    app.run(host="0.0.0.0", port=5000, debug=False)

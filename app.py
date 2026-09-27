from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
import sqlite3
import re
import os
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from pathlib import Path
import base64
import uuid


app = Flask(__name__, static_folder="static", static_url_path="/static")

# ==============================
# Flask 설정
# ==============================

app.secret_key = os.environ.get("SECRET_KEY", "pop-paint-development-secret-key")
app.config["SESSION_COOKIE_SECURE"] = False
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024


# ==============================
# 데이터베이스 / 업로드 폴더
# ==============================

DATABASE = Path(__file__).parent / "database.db"

UPLOAD_FOLDER = (
    Path(__file__).parent
    / "static"
    / "uploads"
)

UPLOAD_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)

app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)


# ==============================
# 업로드된 파일 제공
# ==============================

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):

    safe_name = Path(filename).name
    filepath = UPLOAD_FOLDER / safe_name

    if not filepath.exists():

        return "File not found", 404

    return send_from_directory(
        str(UPLOAD_FOLDER),
        safe_name
    )


# ==============================
# 언어 설정
# ==============================

@app.context_processor
def inject_language():

    return {
        "language": session.get(
            "language",
            "ko"
        )
    }


@app.route("/language/<language>")
def set_language(language):

    if language not in ["ko", "en"]:

        language = "ko"

    session["language"] = language

    return redirect(
        request.referrer
        or url_for("index")
    )


# ==============================
# 데이터베이스 연결
# ==============================

def get_db():

    conn = sqlite3.connect(
        DATABASE
    )

    conn.row_factory = sqlite3.Row

    return conn


# ==============================
# 데이터베이스 초기화
# ==============================

def init_db():

    conn = get_db()

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS accounts (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            account_number TEXT UNIQUE NOT NULL,

            username TEXT UNIQUE NOT NULL,

            password_hash TEXT NOT NULL,

            created_at
            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS drawings (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            account_id INTEGER NOT NULL,

            title TEXT NOT NULL,

            description TEXT,

            filename TEXT NOT NULL,

            uploaded INTEGER DEFAULT 0,

            created_at
            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (account_id)
            REFERENCES accounts(id)
        )
        """
    )

    conn.commit()

    conn.close()


# ==============================
# 로그인 여부 확인
# ==============================

def login_required(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        if "account_id" not in session:

            if (
                request.headers.get("X-Requested-With") == "XMLHttpRequest"
                or "application/json" in request.headers.get("Accept", "")
            ):

                return {
                    "success": False,
                    "message": "로그인이 필요합니다."
                }, 401

            if session.get(
                "language",
                "ko"
            ) == "en":

                flash(
                    "You need to log in."
                )

            else:

                flash(
                    "로그인이 필요합니다."
                )

            return redirect(
                url_for("login")
            )

        return func(
            *args,
            **kwargs
        )

    return wrapper


# ==============================
# 첫 화면
# ==============================

@app.route("/")
def index():

    account = None

    conn = get_db()

    # 로그인한 계정 가져오기
    if "account_id" in session:

        account = conn.execute(
            """
            SELECT *
            FROM accounts
            WHERE id = ?
            """,
            (
                session["account_id"],
            )
        ).fetchone()

    # 검색
    search = request.args.get(
        "search",
        ""
    ).strip()

    if search:

        # 제목이 검색어로 시작하는 그림만 검색
        drawings = conn.execute(
            """
            SELECT
                drawings.*,
                accounts.username,
                accounts.account_number

            FROM drawings

            JOIN accounts
                ON drawings.account_id =
                   accounts.id

            WHERE drawings.uploaded = 1

            AND drawings.title LIKE ? || '%'

            ORDER BY drawings.id DESC
            """,
            (
                search,
            )
        ).fetchall()

    else:

        drawings = conn.execute(
            """
            SELECT
                drawings.*,
                accounts.username,
                accounts.account_number

            FROM drawings

            JOIN accounts
                ON drawings.account_id =
                   accounts.id

            WHERE drawings.uploaded = 1

            ORDER BY drawings.id DESC
            """
        ).fetchall()

    conn.close()

    return render_template(
        "index.html",
        account=account,
        drawings=drawings,
        search=search
    )


# ==============================
# 회원가입
# ==============================

@app.route(
    "/signup",
    methods=["GET", "POST"]
)
def signup():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        language = session.get(
            "language",
            "ko"
        )

        # ==============================
        # 아이디 문자 확인
        # 영어 / 숫자 / _
        # ==============================

        if not re.fullmatch(
            r"[A-Za-z0-9_]+",
            username
        ):

            if language == "en":

                flash(
                    "Username can only contain English letters, numbers, and underscores."
                )

            else:

                flash(
                    "아이디에는 영어, 숫자, 밑줄(_)만 사용할 수 있습니다."
                )

            return redirect(
                url_for("signup")
            )

        # ==============================
        # 아이디 길이
        # ==============================

        if (
            len(username) < 4
            or len(username) > 20
        ):

            if language == "en":

                flash(
                    "Username must be 4 to 20 characters long."
                )

            else:

                flash(
                    "아이디는 4글자 이상 20글자 이하이어야 합니다."
                )

            return redirect(
                url_for("signup")
            )

        # ==============================
        # 비밀번호 문자 확인
        # ==============================

        if not re.fullmatch(
            r"[A-Za-z0-9_]+",
            password
        ):

            if language == "en":

                flash(
                    "Password can only contain English letters, numbers, and underscores."
                )

            else:

                flash(
                    "비밀번호에는 영어, 숫자, 밑줄(_)만 사용할 수 있습니다."
                )

            return redirect(
                url_for("signup")
            )

        # ==============================
        # 비밀번호 길이
        # ==============================

        if (
            len(password) < 8
            or len(password) >= 10
        ):

            if language == "en":

                flash(
                    "Password must be 8 to 9 characters long."
                )

            else:

                flash(
                    "비밀번호는 8글자 이상 10글자 미만이어야 합니다."
                )

            return redirect(
                url_for("signup")
            )

        conn = get_db()

        # ==============================
        # 아이디 중복 검사
        # ==============================

        existing_account = conn.execute(
            """
            SELECT id
            FROM accounts
            WHERE username = ?
            """,
            (
                username,
            )
        ).fetchone()

        if existing_account:

            conn.close()

            if language == "en":

                flash(
                    "That username already exists."
                )

            else:

                flash(
                    "이미 존재하는 아이디입니다."
                )

            return redirect(
                url_for("signup")
            )

        # ==============================
        # 계정 번호 생성
        # ==============================

        last_account = conn.execute(
            """
            SELECT id
            FROM accounts
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

        if last_account:

            next_id = (
                last_account["id"]
                + 1
            )

        else:

            next_id = 1

        account_number = (
            f"POP-{next_id:06d}"
        )

        # ==============================
        # 비밀번호 해시
        # ==============================

        password_hash = (
            generate_password_hash(
                password
            )
        )

        # ==============================
        # 계정 저장
        # ==============================

        conn.execute(
            """
            INSERT INTO accounts
            (
                account_number,
                username,
                password_hash
            )

            VALUES (?, ?, ?)
            """,
            (
                account_number,
                username,
                password_hash
            )
        )

        conn.commit()

        conn.close()

        if language == "en":

            flash(
                f"Sign up complete! Account number: {account_number}"
            )

        else:

            flash(
                f"회원가입 완료! 계정 번호: {account_number}"
            )

        return redirect(
            url_for("login")
        )

    return render_template(
        "signup.html"
    )


# ==============================
# 로그인
# ==============================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        conn = get_db()

        account = conn.execute(
            """
            SELECT *
            FROM accounts
            WHERE username = ?
            """,
            (
                username,
            )
        ).fetchone()

        conn.close()

        # 계정 없음
        if account is None:

            flash(
                "아이디 또는 비밀번호가 올바르지 않습니다."
            )

            return redirect(
                url_for("login")
            )

        # 비밀번호 확인
        if not check_password_hash(
            account["password_hash"],
            password
        ):

            flash(
                "아이디 또는 비밀번호가 올바르지 않습니다."
            )

            return redirect(
                url_for("login")
            )

        # 현재 언어 저장
        selected_language = session.get(
            "language",
            "ko"
        )

        # 기존 세션 초기화
        session.clear()

        session["language"] = (
            selected_language
        )

        session["account_id"] = (
            account["id"]
        )

        session["username"] = (
            account["username"]
        )

        session["account_number"] = (
            account["account_number"]
        )

        return redirect(
            url_for("index")
        )

    return render_template(
        "login.html"
    )


# ==============================
# 비밀번호 변경
# ==============================

@app.route(
    "/change-password",
    methods=["GET", "POST"]
)
@login_required
def change_password():

    if request.method == "POST":

        current_password = request.form.get(
            "current_password",
            ""
        )

        new_password = request.form.get(
            "new_password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        language = session.get(
            "language",
            "ko"
        )

        conn = get_db()

        account = conn.execute(
            """
            SELECT *
            FROM accounts
            WHERE id = ?
            """,
            (
                session["account_id"],
            )
        ).fetchone()

        # 현재 비밀번호 확인
        if not check_password_hash(
            account["password_hash"],
            current_password
        ):

            conn.close()

            if language == "en":

                flash(
                    "Your current password is incorrect."
                )

            else:

                flash(
                    "현재 비밀번호가 올바르지 않습니다."
                )

            return redirect(
                url_for(
                    "change_password"
                )
            )

        # 새 비밀번호 길이
        if (
            len(new_password) < 8
            or len(new_password) >= 10
        ):

            conn.close()

            if language == "en":

                flash(
                    "The new password must be 8 to 9 characters long."
                )

            else:

                flash(
                    "새 비밀번호는 8글자 이상 10글자 미만이어야 합니다."
                )

            return redirect(
                url_for(
                    "change_password"
                )
            )

        # 새 비밀번호 문자
        if not re.fullmatch(
            r"[A-Za-z0-9_]+",
            new_password
        ):

            conn.close()

            if language == "en":

                flash(
                    "Password can only contain English letters, numbers, and underscores."
                )

            else:

                flash(
                    "비밀번호에는 영어, 숫자, 밑줄(_)만 사용할 수 있습니다."
                )

            return redirect(
                url_for(
                    "change_password"
                )
            )

        # 새 비밀번호 확인
        if new_password != confirm_password:

            conn.close()

            if language == "en":

                flash(
                    "The new passwords do not match."
                )

            else:

                flash(
                    "새 비밀번호가 서로 일치하지 않습니다."
                )

            return redirect(
                url_for(
                    "change_password"
                )
            )

        # 해시
        new_password_hash = (
            generate_password_hash(
                new_password
            )
        )

        # DB 업데이트
        conn.execute(
            """
            UPDATE accounts

            SET password_hash = ?

            WHERE id = ?
            """,
            (
                new_password_hash,
                session["account_id"]
            )
        )

        conn.commit()

        conn.close()

        if language == "en":

            flash(
                "Your password has been changed successfully."
            )

        else:

            flash(
                "비밀번호가 성공적으로 변경되었습니다."
            )

        return redirect(
            url_for(
                "account_page",
                username=session["username"]
            )
        )

    return render_template(
        "change_password.html"
    )


# ==============================
# 로그아웃
# ==============================

@app.route("/logout")
def logout():

    language = session.get(
        "language",
        "ko"
    )

    session.clear()

    session["language"] = language

    if language == "en":

        flash(
            "You have been logged out."
        )

    else:

        flash(
            "로그아웃되었습니다."
        )

    return redirect(
        url_for("index")
    )


# ==============================
# 그림 그리기
# ==============================

@app.route("/draw")
@login_required
def draw():

    return render_template(
        "draw.html"
    )


# ==============================
# 그림 저장
# ==============================

@app.route(
    "/save-drawing",
    methods=["POST"]
)
@login_required
def save_drawing():

    data = request.get_json()

    if not data:

        return {
            "success": False,
            "message": "잘못된 요청입니다."
        }, 400

    title = data.get(
        "title",
        ""
    ).strip()

    description = data.get(
        "description",
        ""
    ).strip()

    image_data = data.get(
        "image",
        ""
    )

    # 제목 확인
    if not title:

        return {
            "success": False,
            "message": "제목을 입력해주세요."
        }, 400

    # 그림 확인
    if not image_data:

        return {
            "success": False,
            "message": "그림이 없습니다."
        }, 400

    try:

        # base64 데이터 앞부분 제거
        image_data = image_data.split(
            ",",
            1
        )[1]

        image_bytes = base64.b64decode(
            image_data
        )

    except Exception:

        return {
            "success": False,
            "message": "그림 데이터를 처리할 수 없습니다."
        }, 400

    # 파일명 생성
    filename = (
        str(uuid.uuid4())
        + ".png"
    )

    filepath = (
        UPLOAD_FOLDER
        / filename
    )

    # 이미지 저장
    with open(
        filepath,
        "wb"
    ) as file:

        file.write(
            image_bytes
        )

    # DB 저장
    conn = get_db()

    conn.execute(
        """
        INSERT INTO drawings
        (
            account_id,
            title,
            description,
            filename
        )

        VALUES (?, ?, ?, ?)
        """,
        (
            session["account_id"],
            title,
            description,
            filename
        )
    )

    conn.commit()

    conn.close()

    return {
        "success": True
    }


# ==============================
# 계정 페이지
# ==============================

@app.route(
    "/account/<username>"
)
def account_page(username):

    conn = get_db()

    account = conn.execute(
        """
        SELECT *
        FROM accounts
        WHERE username = ?
        """,
        (
            username,
        )
    ).fetchone()

    if account is None:

        conn.close()

        return "Account not found", 404

    # 해당 계정의 그림
    drawings = conn.execute(
        """
        SELECT *
        FROM drawings

        WHERE account_id = ?

        ORDER BY id DESC
        """,
        (
            account["id"],
        )
    ).fetchall()

    conn.close()

    return render_template(
        "account.html",
        account=account,
        drawings=drawings
    )


# ==============================
# 그림 업로드
# ==============================

@app.route(
    "/upload-drawing/<int:drawing_id>",
    methods=["POST"]
)
@login_required
def upload_drawing(drawing_id):

    conn = get_db()

    # 반드시 현재 로그인한 사람의 그림인지 확인
    drawing = conn.execute(
        """
        SELECT *
        FROM drawings

        WHERE id = ?

        AND account_id = ?
        """,
        (
            drawing_id,
            session["account_id"]
        )
    ).fetchone()

    if drawing is None:

        conn.close()

        return {
            "success": False,
            "message": "그림을 찾을 수 없습니다."
        }, 404

    # 업로드 상태 변경
    conn.execute(
        """
        UPDATE drawings

        SET uploaded = 1

        WHERE id = ?

        AND account_id = ?
        """,
        (
            drawing_id,
            session["account_id"]
        )
    )

    conn.commit()

    conn.close()

    return {
        "success": True
    }


# ==============================
# 그림 삭제
# ==============================

@app.route(
    "/delete-drawing/<int:drawing_id>",
    methods=["POST"]
)
@login_required
def delete_drawing(drawing_id):

    conn = get_db()

    # 현재 로그인한 사람의 그림인지 확인
    drawing = conn.execute(
        """
        SELECT *
        FROM drawings

        WHERE id = ?

        AND account_id = ?
        """,
        (
            drawing_id,
            session["account_id"]
        )
    ).fetchone()

    if drawing is None:

        conn.close()

        return {
            "success": False,
            "message": "그림을 찾을 수 없습니다."
        }, 404

    # 실제 이미지 파일
    filepath = (
        UPLOAD_FOLDER
        / drawing["filename"]
    )

    # 파일 삭제
    try:

        if filepath.exists():

            filepath.unlink()

    except Exception:

        conn.close()

        return {
            "success": False,
            "message": "그림 파일을 삭제할 수 없습니다."
        }, 500

    # 데이터베이스에서 삭제
    conn.execute(
        """
        DELETE FROM drawings

        WHERE id = ?

        AND account_id = ?
        """,
        (
            drawing_id,
            session["account_id"]
        )
    )

    conn.commit()

    conn.close()

    return {
        "success": True
    }


# ==============================
# 그림 상세 보기
# ==============================

@app.route(
    "/drawing/<int:drawing_id>"
)
def drawing_detail(drawing_id):

    conn = get_db()

    drawing = conn.execute(
        """
        SELECT

            drawings.*,

            accounts.username,

            accounts.account_number

        FROM drawings

        JOIN accounts
            ON drawings.account_id =
               accounts.id

        WHERE drawings.id = ?
        """,
        (
            drawing_id,
        )
    ).fetchone()

    conn.close()

    if drawing is None:

        return "Drawing not found", 404

    return render_template(
        "drawing.html",
        drawing=drawing
    )


# ==============================
# 서버 시작
# ==============================

if __name__ == "__main__":

    init_db()

    app.run(
        debug=False,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
from fastapi import FastAPI
import psycopg2

app = FastAPI(title="Университет API")

import os
DB = f"host={os.environ.get('DB_HOST', 'localhost')} port={os.environ.get('DB_PORT', 5432)} dbname={os.environ.get('DB_NAME', 'mf_mgtu')} user={os.environ.get('DB_USER', 'postgres')} password={os.environ.get('DB_PASSWORD', 'postgres')}"

@app.get("/students/{student_id}/grades")
def get_grades(student_id: int):
    with psycopg2.connect(DB) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT d.discipline_name, ct.control_name, gr.semester, gr.grade_value, gr.grade_date
                FROM grades gr
                JOIN discipline_control dc ON gr.discipline_control_id = dc.discipline_control_id
                JOIN disciplines d ON dc.discipline_id = d.discipline_id
                JOIN control_types ct ON dc.control_type_id = ct.control_type_id
                WHERE gr.student_id = %s
                ORDER BY gr.semester
            """, (student_id,))
            return {"student_id": student_id, "grades": cur.fetchall()}

@app.get("/students/{student_id}/debts")
def get_debts(student_id: int):
    with psycopg2.connect(DB) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT d.discipline_name, gr.semester, gr.grade_value
                FROM grades gr
                JOIN discipline_control dc ON gr.discipline_control_id = dc.discipline_control_id
                JOIN disciplines d ON dc.discipline_id = d.discipline_id
                WHERE gr.student_id = %s AND gr.grade_value IN ('2', 'незачтено')
            """, (student_id,))
            return {"student_id": student_id, "debts": cur.fetchall()}

@app.get("/groups/{group_code}/students")
def get_group_students(group_code: str):
    with psycopg2.connect(DB) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT s.full_name, s.status
                FROM students s
                JOIN groups g ON s.group_id = g.group_id
                WHERE g.group_code = %s
            """, (group_code,))
            return {"group": group_code, "students": cur.fetchall()}

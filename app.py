import streamlit as st
import psycopg2
import pandas as pd

DB = {'host': 'localhost', 'port': 5432, 'database': 'mf_mgtu'}

def conn(user, pwd):
    return psycopg2.connect(**DB, user=user, password=pwd)

def q(query, user, pwd, params=None):
    with conn(user, pwd) as c:
        return pd.read_sql_query(query, c, params=params)

def init():
    for k in ['logged_in', 'user', 'pwd', 'role']:
        if k not in st.session_state: st.session_state[k] = None if k != 'logged_in' else False

# Вход в систему
def login():
    st.title(" Университет")
    u = st.text_input("Логин")
    p = st.text_input("Пароль", type="password")
    if st.button("Войти"):
        try:
            conn(u, p).close()
            st.session_state.update(logged_in=True, user=u, pwd=p)
            if u in ['admin_role', 'postgres']: st.session_state.role = 'admin'
            elif u in ['teacher_role', 'prepod_poyarkov']: st.session_state.role = 'teacher'
            else: st.session_state.role = 'student'
            st.rerun()
        except Exception as e:
            st.error(str(e))
    with st.expander("Доступы"):
        st.code("admin_role:admin123\nprepod_poyarkov:prepod123\nivanov:ivanov123\npetrov:petrov123\nsidorov:sidorov123")

# Панель администратора
def admin():
    st.title(" Администратор")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([" Обзор", " Студенты", " Группы", " Оценки", " Пользователи"])

    with tab1:
        c1, c2, c3, c4 = st.columns(4)
        for i, (label, sql) in enumerate([
            ("Студентов", "SELECT COUNT(*) FROM students"),
            (" Групп", "SELECT COUNT(*) FROM groups"),
            (" Дисциплин", "SELECT COUNT(*) FROM disciplines"),
            (" Оценок", "SELECT COUNT(*) FROM grades")
        ]):
            with [c1, c2, c3, c4][i]:
                st.metric(label, q(sql, st.session_state.user, st.session_state.pwd).iloc[0,0])

        st.subheader("Группы")
        st.dataframe(q("""
            SELECT g.group_code, COUNT(s.student_id) AS total,
                   COUNT(*) FILTER (WHERE s.status='active') AS active,
                   COUNT(*) FILTER (WHERE s.status='academic_leave') AS academic,
                   COUNT(*) FILTER (WHERE s.status='expelled') AS expelled
            FROM groups g LEFT JOIN students s ON g.group_id=s.group_id
            GROUP BY g.group_code ORDER BY g.group_code
        """, st.session_state.user, st.session_state.pwd), use_container_width=True)

    with tab2:
        st.subheader("Все студенты")
        df = q("""
            SELECT s.student_id, s.full_name, g.group_code, s.status, s.record_book_num
            FROM students s JOIN groups g ON s.group_id=g.group_id
            ORDER BY g.group_code, s.full_name
        """, st.session_state.user, st.session_state.pwd)
        st.dataframe(df, use_container_width=True)

        st.divider()

        st.subheader(" Изменить студента")
        sid = st.selectbox("Студент", df['student_id'].tolist(),
                          format_func=lambda x: f"{df[df['student_id']==x]['full_name'].iloc[0]} ({df[df['student_id']==x]['group_code'].iloc[0]})",
                          key="edit_student_select")
        if sid:
            info = df[df['student_id'] == sid].iloc[0]
            c1, c2 = st.columns(2)
            with c1:
                new_status = st.selectbox("Статус", ['active','academic_leave','expelled'],
                                         index=['active','academic_leave','expelled'].index(info['status']),
                                         key="edit_student_status")
            with c2:
                groups_list = q("SELECT group_code FROM groups ORDER BY group_code",
                               st.session_state.user, st.session_state.pwd)['group_code'].tolist()
                new_group = st.selectbox("Группа", groups_list,
                                        index=groups_list.index(info['group_code']),
                                        key="edit_student_group")
            if st.button(" Сохранить изменения", key="save_student_btn"):
                with conn(st.session_state.user, st.session_state.pwd) as c:
                    cur = c.cursor()
                    cur.execute("SELECT group_id FROM groups WHERE group_code=%s", (new_group,))
                    gid = cur.fetchone()[0]
                    cur.execute("UPDATE students SET status=%s, group_id=%s WHERE student_id=%s", (new_status, gid, sid))
                    c.commit()
                st.success("Сохранено!")
                st.rerun()

        st.divider()

        st.subheader(" Отчислить студента")
        del_sid = st.selectbox("Выбери студента для отчисления", df['student_id'].tolist(),
                               format_func=lambda x: f"{df[df['student_id']==x]['full_name'].iloc[0]} ({df[df['student_id']==x]['group_code'].iloc[0]})",
                               key="delete_student_select")
        reason = st.text_input("Причина отчисления", placeholder="Академическая неуспеваемость / По собственному желанию / ...", key="delete_reason")

        if st.button(" Отчислить", key="delete_student_btn"):
            if reason:
                with conn(st.session_state.user, st.session_state.pwd) as c:
                    cur = c.cursor()
                    cur.execute("""
                        UPDATE students
                        SET status='expelled', expelled_date=CURRENT_DATE, expulsion_reason=%s
                        WHERE student_id=%s
                    """, (reason, del_sid))
                    c.commit()
                st.success(f"Студент отчислен! Причина: {reason}")
                st.rerun()
            else:
                st.error("Укажи причину отчисления!")

        st.divider()

        st.subheader(" Добавить студента")
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("ФИО", key="add_name")
            rec = st.text_input("Зачётка", key="add_rec")
        with c2:
            grp_new = st.selectbox("Группа для нового", q("SELECT group_code FROM groups ORDER BY group_code",
                                   st.session_state.user, st.session_state.pwd)['group_code'].tolist(), key="add_group")
            phone = st.text_input("Телефон", key="add_phone")
        if st.button(" Добавить", key="add_student_btn"):
            with conn(st.session_state.user, st.session_state.pwd) as c:
                cur = c.cursor()
                cur.execute("SELECT group_id FROM groups WHERE group_code=%s", (grp_new,))
                gid = cur.fetchone()[0]
                cur.execute("""
                    INSERT INTO students (full_name, record_book_num, group_id, phone, email, enrollment_date, status)
                    VALUES (%s, %s, %s, %s, LOWER(SPLIT_PART(%s,' ',2)||'.'||SPLIT_PART(%s,' ',1)||'@mfua.ru'), CURRENT_DATE, 'active')
                    RETURNING student_id
                """, (name, rec, gid, phone, name, name))
                new_id = cur.fetchone()[0]
                c.commit()
            st.success(f"Студент {name} добавлен! ID: {new_id}")
            st.rerun()

    with tab3:
        st.subheader("Управление группами")
        df_g = q("SELECT * FROM groups ORDER BY group_code", st.session_state.user, st.session_state.pwd)
        st.dataframe(df_g, use_container_width=True)

        st.subheader(" Добавить группу")
        c1, c2 = st.columns(2)
        with c1:
            gc = st.text_input("Код группы", placeholder="К3-36Б", key="add_group_code")
        with c2:
            fac = st.selectbox("Факультет", q("SELECT faculty_code FROM faculties",
                               st.session_state.user, st.session_state.pwd)['faculty_code'].tolist(), key="add_group_fac")
        ey = st.number_input("Год поступления", 2020, 2030, 2025, key="add_group_year")
        spec = st.text_input("Специальность", key="add_group_spec")
        if st.button(" Добавить группу", key="add_group_btn"):
            with conn(st.session_state.user, st.session_state.pwd) as c:
                cur = c.cursor()
                cur.execute("SELECT faculty_id FROM faculties WHERE faculty_code=%s", (fac,))
                fid = cur.fetchone()[0]
                cur.execute("INSERT INTO groups (group_code, faculty_id, enrollment_year, specialty_name) VALUES (%s,%s,%s,%s)",
                           (gc, fid, ey, spec))
                c.commit()
            st.success("Группа добавлена!")
            st.rerun()

    with tab4:
        st.subheader("Ведомость")
        grp_sel = st.selectbox("Группа", q("SELECT DISTINCT \"Группа\" FROM v_teacher_grades",
                               st.session_state.user, st.session_state.pwd)["Группа"].tolist(), key="admin_grades")
        df_v = q(f"SELECT * FROM v_teacher_grades WHERE \"Группа\"=%s", st.session_state.user, st.session_state.pwd, (grp_sel,))
        st.dataframe(df_v, use_container_width=True)

        if not df_v.empty:
            st.subheader(" Изменить оценку")
            gid = st.number_input("grade_id", min_value=int(df_v['grade_id'].min()), max_value=int(df_v['grade_id'].max()), key="admin_grade_id")
            ng = st.selectbox("Новая оценка", ['5','4','3','2','зачтено','незачтено','НА'], key="admin_grade_val")
            if st.button(" Обновить оценку", key="admin_save_grade"):
                with conn(st.session_state.user, st.session_state.pwd) as c:
                    c.cursor().execute("UPDATE grades SET grade_value=%s, grade_date=CURRENT_DATE WHERE grade_id=%s", (ng, gid))
                    c.commit()
                st.success("Готово!")
                st.rerun()

    with tab5:
        st.subheader(" Управление пользователями")

        st.write("**Студенты с доступом:**")
        df_users = q("""
            SELECT us.user_login, s.student_id, s.full_name, g.group_code
            FROM user_student us
            JOIN students s ON us.student_id = s.student_id
            JOIN groups g ON s.group_id = g.group_id
            ORDER BY us.user_login
        """, st.session_state.user, st.session_state.pwd)
        st.dataframe(df_users, use_container_width=True)

        st.divider()

        st.subheader(" Привязать пользователя к студенту")
        c1, c2 = st.columns(2)
        with c1:
            new_login = st.text_input("Логин (латиница)", placeholder="student1", key="user_login")
            new_pass = st.text_input("Пароль", type="password", key="user_pass")
        with c2:
            free_students = q("""
                SELECT s.student_id, s.full_name, g.group_code
                FROM students s
                JOIN groups g ON s.group_id = g.group_id
                WHERE s.student_id NOT IN (SELECT student_id FROM user_student)
                ORDER BY g.group_code, s.full_name
            """, st.session_state.user, st.session_state.pwd)

            if not free_students.empty:
                selected_student = st.selectbox(
                    "Студент",
                    free_students['student_id'].tolist(),
                    format_func=lambda x: f"{free_students[free_students['student_id']==x]['full_name'].iloc[0]} ({free_students[free_students['student_id']==x]['group_code'].iloc[0]})",
                    key="select_free_student"
                )
            else:
                st.warning("Нет свободных студентов")
                selected_student = None

        if st.button(" Создать студента", key="create_student_user"):
            if new_login and new_pass and selected_student:
                with conn(st.session_state.user, st.session_state.pwd) as c:
                    cur = c.cursor()
                    try:
                        cur.execute(f"CREATE ROLE {new_login} WITH LOGIN PASSWORD %s IN ROLE student_role", (new_pass,))
                        cur.execute("INSERT INTO user_student (user_login, student_id) VALUES (%s, %s)", (new_login, selected_student))
                        c.commit()
                        st.success(f"Студент {new_login} создан!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Ошибка: {e}")
            else:
                st.error("Заполни все поля!")

        st.divider()

        st.subheader(" Создать преподавателя")
        c1, c2 = st.columns(2)
        with c1:
            teacher_login = st.text_input("Логин", placeholder="prepod2", key="teacher_login")
            teacher_pass = st.text_input("Пароль", type="password", key="teacher_pass")
        with c2:
            teacher_name = st.text_input("ФИО (для справки)", key="teacher_name")

        if st.button(" Создать преподавателя", key="create_teacher_btn"):
            if teacher_login and teacher_pass:
                with conn(st.session_state.user, st.session_state.pwd) as c:
                    cur = c.cursor()
                    try:
                        cur.execute(f"CREATE ROLE {teacher_login} WITH LOGIN PASSWORD %s IN ROLE teacher_role", (teacher_pass,))
                        c.commit()
                        st.success(f"Преподаватель {teacher_login} создан!")
                    except Exception as e:
                        st.error(f"Ошибка: {e}")
            else:
                st.error("Заполни логин и пароль!")

        st.divider()

        st.subheader(" Удалить привязку студента")
        if not df_users.empty:
            del_login = st.selectbox("Выбери пользователя для удаления", df_users['user_login'].tolist(), key="del_user")
            if st.button(" Удалить привязку", key="delete_user_btn"):
                with conn(st.session_state.user, st.session_state.pwd) as c:
                    cur = c.cursor()
                    cur.execute("DELETE FROM user_student WHERE user_login = %s", (del_login,))
                    cur.execute(f"DROP ROLE IF EXISTS {del_login}")
                    c.commit()
                st.success(f"Пользователь {del_login} удалён!")
                st.rerun()

# Панель преподавателя
def teacher():
    st.title(" Преподаватель")
    tab1, tab2 = st.tabs(["Группы", "Ведомость"])
    with tab1:
        st.dataframe(q("SELECT * FROM v_teacher_groups", st.session_state.user, st.session_state.pwd), use_container_width=True)
    with tab2:
        grp = st.selectbox("Группа", q("SELECT DISTINCT \"Группа\" FROM v_teacher_grades", st.session_state.user, st.session_state.pwd)["Группа"].tolist())
        df = q(f"SELECT * FROM v_teacher_grades WHERE \"Группа\" = %s", st.session_state.user, st.session_state.pwd, (grp,))
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            gid = st.number_input("grade_id для изменения", min_value=int(df['grade_id'].min()), max_value=int(df['grade_id'].max()))
            ng = st.selectbox("Оценка", ['5','4','3','2','зачтено','незачтено','НА'])
            if st.button("Обновить"):
                with conn(st.session_state.user, st.session_state.pwd) as c:
                    c.cursor().execute("UPDATE grades SET grade_value=%s, grade_date=CURRENT_DATE WHERE grade_id=%s", (ng, gid))
                    c.commit()
                st.success("Готово!")

# Панель студента
def student():
    st.title(" Студент")
    df = q("SELECT * FROM v_my_grades ORDER BY \"Семестр\", \"Предмет\"", st.session_state.user, st.session_state.pwd)
    if df.empty: st.warning("Нет оценок")
    else:
        c1, c2 = st.columns(2)
        c1.metric("Предметов", len(df))
        c2.metric("Долгов", len(df[df['Оценка'].isin(['2','незачтено'])]))
        st.dataframe(df, use_container_width=True)

def main():
    st.set_page_config(page_title="Универ", layout="wide")
    init()
    if not st.session_state.logged_in:
        login()
    else:
        with st.sidebar:
            st.success(st.session_state.user)
            if st.button("Выйти"):
                st.session_state.logged_in = False
                st.rerun()
        {'admin': admin, 'teacher': teacher, 'student': student}[st.session_state.role]()

if __name__ == "__main__":
    main()

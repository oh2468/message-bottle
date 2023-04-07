import sqlite3
import time
import random


class DBHandler():

    def __init__(self):
        self.conn = sqlite3.connect("MESSAGE_BOTTLE.db")
        self.cur = self.conn.cursor()
        self.create_table()
        print("Now connected to the DB!")


    def __del__(self):
        self.cur.close()
        self.conn.close()
        print("Now closed the DB connection!")


    def get_moment_in_time(self):
        return time.time()


    def create_table(self):
        self.cur.execute("""CREATE TABLE IF NOT EXISTS bottle(
            sender VARCHAR(30) NOT NULL,
            title VARCHAR(30) NOT NULL,
            message TEXT NOT NULL,
            posted DATETIME NOT NULL,
            available DATETIME NOT NULL,
            password VARCHAR(255),
            salt VARCHAR(255));"""
        )

        self.conn.commit()

    
    def insert_message(self, sender, title, message, available, password=None, salt=None):
        day = 24 * 60 * 60
        po_stamp = self.get_moment_in_time()
        av_stamp = po_stamp + (int(available) * day)
        self.cur.execute("INSERT INTO bottle VALUES (?, ?, ?, ?, ?, ?, ?)", (sender, title, message, po_stamp, av_stamp, password, salt))
        self.conn.commit()


    def shuffle_private_messages(self, msgs):
        public_msgs = [msg for msg in msgs if msg[3]]
        private_msgs = [msg for msg in msgs if not msg[3]]
        random.shuffle(private_msgs)
        return public_msgs + private_msgs


    def get_messages(self, col_sort, dir_sort, limit=5, offset=0, send_f="", titl_f="", messa_f=""):
        print(f"column: {col_sort}, dir: {dir_sort}")

        now = self.get_moment_in_time()
        text_columns = ["sender", "title", "message"]
        col_sort_mod = f"lower({col_sort})" if col_sort in text_columns else col_sort
        salt_sort = 'salt ASC,' if col_sort == 'message' else ''

        base_query = """FROM bottle WHERE available >= ? AND 
            sender LIKE ('%' || ? || '%') AND 
            title LIKE ('%' || ? || '%') AND 
            message LIKE ('%' || ? || '%')"""

        if messa_f:
            base_query = f"{base_query} AND password IS NULL"


        count_query = f"SELECT COUNT(*) {base_query};"
        msg_query = f"""SELECT rowid, sender, title, CASE WHEN password IS NULL THEN message ELSE '' END, posted, available 
            {base_query} 
            ORDER BY {salt_sort} {col_sort_mod} {dir_sort}
            LIMIT ? 
            OFFSET ?;"""

        tot_msgs = self.get_total_message_count(now)
        num_msgs = self.cur.execute(count_query, (now, send_f, titl_f, messa_f)).fetchone()[0]
        messages = self.cur.execute(msg_query, (now, send_f, titl_f, messa_f, limit, offset)).fetchall()

        if col_sort == "message": 
            messages = self.shuffle_private_messages(messages)

        return (num_msgs, tot_msgs, messages)


    def get_password_and_salt(self, row_id):
        return self.cur.execute("SELECT password, salt FROM bottle WHERE rowid = ?", (row_id, )).fetchone()


    def get_total_message_count(self, time_stamp):
        return self.cur.execute("SELECT COUNT(*) FROM bottle WHERE available >= ?", (time_stamp, )).fetchone()[0]


    def get_message_content(self, row_id):
        return self.cur.execute("SELECT message FROM bottle WHERE rowid = ?", (row_id, )).fetchone()[0]


    def delete_old_messages(self, time_stamp=None):
        now = time_stamp or self.get_moment_in_time()
        self.cur.execute("DELETE FROM bottle WHERE available < ?", (now, ))
        self.conn.commit()



from sqlalchemy import create_engine, text
import os

db_connection_string = os.environ['DB_CONNECTION_STRING']

engine = create_engine(db_connection_string)

def load_jobs_from_db():
  with engine.connect() as conn:
    result=conn.execute(text("select * from users limit 5"))
    jobs=[]
    for row in result.all():
      jobs.append(row._asdict())
    return jobs


def load_job_from_db(id):
  with engine.connect()  as conn:
    result = conn.execute(
        text("select * from users where id = :val").params(val=id)
    )

    rows=result.all()                    
    if len(rows)==0:
      return None
    else:
      return rows[0]._asdict()


def add_application_to_db(job_id, data):
  with engine.connect() as conn:
    query = text("INSERT INTO Users (first_name, last_name, username, email, password, address) VALUES (:first_name, :last_name, :username, :email, :password, :address)")

    conn.execute(query, {
        'first_name': data['first_name'],
        'last_name': data['last_name'],
        'username': data['username'],
        'email': data['email'],
        'password': data['password'],
        'address': data['address']
    })
  

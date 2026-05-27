import pyodbc

def run_etl():
    conn = pyodbc.connect(
        "DRIVER={SQL Server};SERVER=localhost;DATABASE=master;Trusted_Connection=yes;"
    )
    cursor = conn.cursor()

    print("Running ETL...")
    cursor.execute("EXEC sp_run_full_etl;")
    conn.commit()

    print("ETL completed!")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    run_etl()
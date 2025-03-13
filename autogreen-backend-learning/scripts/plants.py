import csv
from google.cloud.sql.connector import Connector, IPTypes
import psycopg2

# Database connection details for RDS
DB_HOST = "autogreen-db-1.clk2q8i2c4nk.us-east-1.rds.amazonaws.com"  # Replace with your RDS endpoint
DB_PORT = 5432  # Default PostgreSQL port
DB_NAME = "postgres"  # Replace with your database name
DB_USER = "autogreen_user"  # Replace with your username
DB_PASSWORD = "ILoveTheLibrary765$"  # Replace with your password

conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
cursor = conn.cursor()

# Read the CSV file
csv_file_path = "house_plants.csv"
plants = []
with open(csv_file_path, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        plants.append(row)

# Insert plants into the database


def delete_plants():
    # Delete all rows from the plants table
    delete_query = "DELETE FROM plants"
    cursor.execute(delete_query)

    # Commit the transaction and close the connection
    conn.commit()

def insert_plants():

    insert_query = """
    INSERT INTO plants (plant_id, species_name, min_temp_range, max_temp_range, watering_frequency, watering_amount, plant_moisture_level)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    count = 2
    for plant in plants:
        cursor.execute(insert_query, (
            str(count),
            plant['species_name'],
            int(plant['min_temp_range']),
            int(plant['max_temp_range']),
            plant['watering_frequency'],
            int(plant['watering_amount']),
            int(plant['plant_moisture_level'])
        ))
        count += 1

    conn.commit()
    cursor.close()
    conn.close()


# Run the insert function
if __name__ == "__main__":
    delete_plants()
    insert_plants()

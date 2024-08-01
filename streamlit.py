import streamlit as st
from pymongo import MongoClient, errors
import pandas as pd
from io import BytesIO

# MongoDB Connection with Increased Timeout and SSL Disabled for Testing
try:
    client = MongoClient(
        "mongodb+srv://ben:hixUhNKprbZuZtAn@doctorsdb.ryjys62.mongodb.net/?retryWrites=true&w=majority&appName=doctorsdb",
        tls=True,
        tlsAllowInvalidCertificates=True,  # Disable SSL verification for testing
        serverSelectionTimeoutMS=60000  # Increase timeout to 60 seconds
    )
    db = client['doctors']
    offices_collection = db['offices']
    st.success("Connected to MongoDB successfully.")
except errors.ServerSelectionTimeoutError as err:
    st.error(f"Server selection timeout error: {err}")
except Exception as e:
    st.error(f"An error occurred: {e}")

st.title("Doctor Offices Overview")

st.header("Filter Options")

search_by_num_doctors = st.checkbox("Filter by Number of Doctors")
input_num_doctors = st.number_input("Max Number of Doctors:", min_value=0, value=0, key="num_doctors") if search_by_num_doctors else 0

search_by_num_doctors_cert_after_2019 = st.checkbox("Filter by Doctors Certified After 2019")
input_num_doctors_cert_after_2019 = st.number_input("Min Number Certified After 2019:", min_value=0, value=0, key="cert_after_2019") if search_by_num_doctors_cert_after_2019 else 0

filter_by_city = st.checkbox("Filter by City")
input_city = st.text_input("City:", value="", max_chars=100, key="city").upper() if filter_by_city else ""

filter_by_state = st.checkbox("Filter by State (ABV)")
input_state = st.text_input("State:", value="", max_chars=2, key="state").upper() if filter_by_state else ""

filter_by_zipcode = st.checkbox("Filter by Zipcode")
input_zipcode = st.text_input("Zipcode:", value="", max_chars=10, key="zipcode").upper() if filter_by_zipcode else ""

if st.button('Run Query'):
    query = {}
    if search_by_num_doctors:
        query["doctor_count"] = {"$lte": input_num_doctors}
    if search_by_num_doctors_cert_after_2019:
        query["doctors_certified_2019_or_later"] = {"$gte": input_num_doctors_cert_after_2019}
    if filter_by_city and input_city:
        query["city"] = input_city
    if filter_by_state and input_state:
        query["state"] = input_state
    if filter_by_zipcode and input_zipcode:
        query["postal_code"] = input_zipcode

    try:
        office_results = offices_collection.find(query)
        office_results_list = list(office_results)
        st.session_state.office_results_list = office_results_list
    except Exception as e:
        st.error(f"An error occurred while querying: {e}")

if 'office_results_list' in st.session_state:
    office_results_list = st.session_state.office_results_list
    
    if len(office_results_list) > 0:
        data = []
        for office in office_results_list:
            postal_code = str(office['postal_code']).rstrip('.').split('.')[0]
            formatted_zipcode = '-'.join([postal_code[:5], postal_code[5:]]) if len(postal_code) > 5 else postal_code
            address_lines = [
                f"{office['address']},",
                f"{office['city']},",
                f"{office['state']}, {formatted_zipcode}"
            ]
            formatted_address = '\n'.join(line for line in address_lines if line)
            data.append({
                "Office Name": office['office_name'],
                "Address": formatted_address,
                "Total Doctors": office['doctor_count'],
                "Doctors Certified After 2019": office['doctors_certified_2019_or_later']
            })
            st.subheader(f"Office Name: {office['office_name']}")
            st.write(f"Address:\n{formatted_address}")
            st.write(f"Total Doctors: {office['doctor_count']}")
            st.write(f"Doctors Certified After 2019: {office['doctors_certified_2019_or_later']}")
            st.markdown("---")
        
        df = pd.DataFrame(data)
        
        def to_excel(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Sheet1')
            processed_data = output.getvalue()
            return processed_data
        
        st.download_button(
            label="Download Results as Excel",
            data=to_excel(df),
            file_name='doctor_offices.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    else:
        st.write("No matching records found.")

client.close()

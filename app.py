import pandas as pd
from datetime import datetime
import streamlit as st
from io import StringIO, BytesIO

def create_dict_from_lines(uploaded_files, search_strings, start_time, end_time):
    count_dict = {search_string: {} for search_string in search_strings}
    
    for uploaded_file in uploaded_files:
        file_content = StringIO(uploaded_file.getvalue().decode("utf-8"))
        for line in file_content:
            try:
                timestamp_str = ' '.join(line.split()[:2])
                try:
                    timestamp = datetime.strptime(timestamp_str, '%d:%b:%Y %H:%M:%S.%f')
                except ValueError:
                    continue
                
                if start_time <= timestamp <= end_time:
                    for search_string in search_strings:
                        if search_string in line:
                            call_by_start = line.find("call by") + len("call by ")
                            call_by_end = line.find(' ', call_by_start)
                            call_by_value = line[call_by_start:call_by_end]
                            
                            if call_by_value not in count_dict[search_string]:
                                count_dict[search_string][call_by_value] = 0
                            count_dict[search_string][call_by_value] += 1
            except Exception as e:
                st.error(f"Error processing line: {line}\nError: {e}")

    return count_dict

def export_to_excel(dictionary):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for search_string, call_by_counts in dictionary.items():
            data = [[call_by_value, count] for call_by_value, count in call_by_counts.items()]
            df = pd.DataFrame(data, columns=['Call By', 'Count'])
            safe_search_string = search_string.replace('/', '_').replace(':', '_').replace('"', '').replace(',', '').replace('{', '').replace('}', '').replace('path', 'p').replace('method', 'm')
            df.to_excel(writer, sheet_name=safe_search_string, index=False)
    output.seek(0)
    return output

def process_files(uploaded_files, search_strings, start_time, end_time, file_name):
    result_dict = create_dict_from_lines(uploaded_files, search_strings, start_time, end_time)
    excel_data = export_to_excel(result_dict)
    
    st.download_button(
        label="Download Excel File",
        data=excel_data,
        file_name=f"{file_name}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Streamlit app
st.title("Log File Processor")
st.write("This is a log processor for client API requests only.")

uploaded_files = st.file_uploader("Upload Log Files", accept_multiple_files=True, type=["txt", "log"])

start_time_str = st.text_input("Start Time (dd:MMM:yyyy HH:MM:SS)", value='02:Sep:2024 00:00:00')
end_time_str = st.text_input("End Time (dd:MMM:yyyy HH:MM:SS)", value='02:Sep:2024 23:59:00')

try:
    start_time = datetime.strptime(start_time_str, '%d:%b:%Y %H:%M:%S')
    end_time = datetime.strptime(end_time_str, '%d:%b:%Y %H:%M:%S')
except ValueError:
    st.error("Please enter a valid date format (dd:MMM:yyyy HH:MM:SS)")

search_strings = [
    '{"path":"/orders","method":"POST"',
    '{"path":"/orders","method":"GET",',
    '{"path":"/portfolio/positions","method":"GET",',
    '{"path":"/orders/trades","method":"GET"',
    '"path":"/user/balance","method":"GET"',
    '{"path":"/portfolio/holdings","method":"GET"',
    '{"path":"/orders","method":"PUT"',
    '{"path":"/orders","method":"DELETE"',
    '"method":"GET"'
]

file_name = st.text_input("Filename", value="processed_log")

if st.button("Process Files") and uploaded_files:
    process_files(uploaded_files, search_strings, start_time, end_time, file_name)

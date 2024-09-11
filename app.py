import pandas as pd
from datetime import datetime
import streamlit as st
from io import StringIO, BytesIO

# Dictionary to map user-friendly search strings to actual strings
search_string_map = {
    "POST Order": '{"path":"/orders","method":"POST"',
    "GET Order": '{"path":"/orders","method":"GET",',
    "GET Portfolio Positions": '{"path":"/portfolio/positions","method":"GET",',
    "GET Order Trades": '{"path":"/orders/trades","method":"GET"',
    "GET User Balance": '"path":"/user/balance","method":"GET"',
    "GET Portfolio Holdings": '{"path":"/portfolio/holdings","method":"GET"',
    "PUT Order": '{"path":"/orders","method":"PUT"',
    "DELETE Order": '{"path":"/orders","method":"DELETE"',
    "GET Request (Generic)": '"method":"GET"',
}


def create_dict_from_lines(uploaded_files, search_strings, start_time, end_time):
    count_dict = {search_string: {} for search_string in search_strings}

    for uploaded_file in uploaded_files:
        file_content = StringIO(uploaded_file.getvalue().decode("utf-8"))
        for line in file_content:
            try:
                timestamp_str = " ".join(line.split()[:2])
                try:
                    timestamp = datetime.strptime(timestamp_str, "%d:%b:%Y %H:%M:%S.%f")
                except ValueError:
                    continue

                if start_time <= timestamp <= end_time:
                    for search_string in search_strings:
                        if search_string in line:
                            call_by_start = line.find("call by") + len("call by ")
                            call_by_end = line.find(" ", call_by_start)
                            call_by_value = line[call_by_start:call_by_end]

                            if call_by_value not in count_dict[search_string]:
                                count_dict[search_string][call_by_value] = 0
                            count_dict[search_string][call_by_value] += 1
            except Exception as e:
                st.error(f"Error processing line: {line}\nError: {e}")

    return count_dict


def export_to_excel(dictionary, selected_labels):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        # Loop through each search string and its corresponding count dictionary
        for label, search_string in selected_labels.items():
            call_by_counts = dictionary[search_string]

            # Convert the data into a sorted DataFrame by count in descending order
            data = sorted(call_by_counts.items(), key=lambda x: x[1], reverse=True)
            df = pd.DataFrame(data, columns=["Call By", "Count"])

            # Write the DataFrame to Excel using the user-friendly label as the sheet name
            safe_label = (
                label.replace("/", "_")
                .replace(":", "_")
                .replace('"', "")
                .replace(",", "")
                .replace("{", "")
                .replace("}", "")
                .replace("path", "p")
                .replace("method", "m")
            )
            df.to_excel(writer, sheet_name=safe_label, index=False)

    output.seek(0)
    return output


def process_files(
    uploaded_files, search_strings, start_time, end_time, file_name, selected_labels
):
    result_dict = create_dict_from_lines(
        uploaded_files, search_strings, start_time, end_time
    )
    excel_data = export_to_excel(result_dict, selected_labels)

    st.download_button(
        label="Download Excel File",
        data=excel_data,
        file_name=f"{file_name}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# Streamlit app
st.title("Log File Processor")
st.write("This is a log processor for client API requests only.")

uploaded_files = st.file_uploader(
    "Upload Log Files", accept_multiple_files=True, type=["txt", "log"]
)

today_date = datetime.now().strftime("%d:%b:%Y")
start_time_str = st.text_input(
    "Start Time (dd:MMM:yyyy HH:MM:SS)", value=f"{today_date} 00:00:00"
)
end_time_str = st.text_input(
    "End Time (dd:MMM:yyyy HH:MM:SS)", value=f"{today_date} 23:59:00"
)

try:
    start_time = datetime.strptime(start_time_str, "%d:%b:%Y %H:%M:%S")
    end_time = datetime.strptime(end_time_str, "%d:%b:%Y %H:%M:%S")
except ValueError:
    st.error("Please enter a valid date format (dd:MMM:yyyy HH:MM:SS)")

# Display checkboxes for search strings
selected_search_strings = []
selected_labels = {}
st.write("Select search strings to include:")
for label, search_string in search_string_map.items():
    if st.checkbox(label, value=True):
        selected_search_strings.append(search_string)
        selected_labels[label] = search_string

file_name = st.text_input("Filename", value="processed_log")

if st.button("Process Files") and uploaded_files and selected_search_strings:
    process_files(
        uploaded_files,
        selected_search_strings,
        start_time,
        end_time,
        file_name,
        selected_labels,
    )

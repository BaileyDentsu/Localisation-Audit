import streamlit as st
import pandas as pd
import openai
from io import StringIO
import time

# User input for API key
api_key = st.text_input("Enter your OpenAI API key", type="password")

# Check if the API key is provided
if api_key:
    openai.api_key = api_key
    
    # Load CSV file
    uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

    # Check if file is uploaded
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        
        # Multiselect columns
        selected_columns = st.multiselect("Select the columns you want to concatenate", df.columns)
        
        # Allow prompt customization
        prompt_template = st.text_area(
            "Customize your prompt",
            value="work out the percentage of each language used in this string: {Concat}. Return the output in this format: en: 20%, de: 80%."
        )
        
        # Button to start analysis
        if st.button("Analyse"):
            if selected_columns:
                # Concatenating the selected columns
                df['Concatenated'] = df[selected_columns].apply(lambda row: '. '.join(row.values.astype(str)), axis=1)
                
                # Progress bar for long operations
                progress_bar = st.progress(0)
                results = []
                
                # Function to send prompt to OpenAI
                def get_openai_response(text, prompt_template):
                    prompt = prompt_template.replace("{Concat}", text)
                    try:
                        response = openai.Completion.create(
                            engine="text-davinci-003",  # Choose the model
                            prompt=prompt,
                            max_tokens=60,
                            n=1,
                            stop=None,
                            temperature=0.5
                        )
                        return response.choices[0].text.strip()
                    except Exception as e:
                        return f"Error: {e}"
                
                # Loop over rows and get API responses
                for idx, row in df.iterrows():
                    response = get_openai_response(row['Concatenated'], prompt_template)
                    results.append(response)
                    progress_bar.progress((idx + 1) / len(df))
                    time.sleep(0.18)  # Adjusted delay to 0.18 seconds to stay within rate limits
                
                # Add responses to DataFrame
                df['OpenAI_Response'] = results
                
                # Display the updated DataFrame
                st.write(df)

                # Option to download the new DataFrame with responses
                csv = df.to_csv(index=False)
                st.download_button("Download CSV", data=csv, mime='text/csv')
            else:
                st.warning("Please select at least one column to concatenate.")
    else:
        st.info("Upload a CSV file to begin.")
else:
    st.info("Please enter your OpenAI API key.")

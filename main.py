import streamlit as st
import pandas as pd
import openai
import time

# List of officially supported languages by GPT-4 (commonly supported by models)
SUPPORTED_LANGUAGES = ["en", "fr", "de", "es", "it", "pt", "ru", "zh", "ja", "ko", "ar", "nl", "sv", "no", "da"]

# User input for API key
api_key = st.text_input("Enter your OpenAI API key", type="password")

# Check if the API key is provided
if api_key:
    openai.api_key = api_key
    
    # Load CSV file
    uploaded_file = st.file_uploader("Upload your CSV or Excel file", type=["csv", "xlsx"])

    # Check if file is uploaded
    if uploaded_file is not None:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
        
        # Multiselect columns
        selected_columns = st.multiselect("Select the columns you want to concatenate", df.columns)
        
        # Allow user to select which languages to detect
        selected_languages = st.multiselect(
            "Select the languages to detect",
            SUPPORTED_LANGUAGES,
            default=["en", "fr", "de"]
        )
        
        # Format the languages for the prompt (e.g., 'en, fr, de')
        language_scope = ', '.join(selected_languages)

        # Allow prompt customization
        prompt_template = st.text_area(
            "Customize your prompt",
            value=f"Input: {{inputText}}. Task 1: Remove company branding, keep product branding. "
                  f"Task 2: Return language percentages ({language_scope}) in this format: en: 20%, fr: 40%. "
                  "Omit 0%. Ensure total = 100%. Only return task 2."
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
                def get_openai_response(language_scope, text, prompt_template):
                    prompt = prompt_template.replace("{inputText}", text)
                    prompt = prompt_template.replace("{language_scope}", language_scope)
                    try:
                        response = openai.Completion.create(
                            engine="gpt-4o",  # Using GPT-4o model
                            prompt=prompt,
                            max_tokens=100,
                            n=1,
                            stop=None,
                            temperature=0.5
                        )
                        return response.choices[0].text.strip()
                    except Exception as e:
                        return f"Error: {e}"
                
                # Loop over rows and get API responses
                for idx, row in df.iterrows():
                    response = get_openai_response(language_scope, row['Concatenated'], prompt_template)
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

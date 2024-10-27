import http.client
import json
import re
import streamlit as st
from langchain_groq import ChatGroq

# Define the agents
class IndustryResearchAgent:
    def __init__(self, api_key):
        self.api_key = api_key

    def research(self, company_name):
        """Researches the industry or company to gather relevant information."""
        try:
            conn = http.client.HTTPSConnection("google.serper.dev")
            payload = json.dumps({"q": company_name})
            
            headers = {
                'X-API-KEY': self.api_key,
                'Content-Type': 'application/json'
            }
            
            conn.request("POST", "/search", payload, headers)
            res = conn.getresponse()
            
            if res.status == 403:
                raise PermissionError("Unauthorized access: 403 Forbidden.")
            
            data = res.read()
            response_data = json.loads(data.decode("utf-8"))
            
            return response_data
        
        except Exception as e:
            st.error(f"Error during industry research: {e}")
            return None

class LinkExtractionAgent:
    @staticmethod
    def extract_links(reference_links):
        """Extracts Kaggle, GitHub, and Hugging Face links from reference links."""
        extracted_links = []
        for link in reference_links:
            found_links = re.findall(r'https?://(?:www\.)?(kaggle\.com|github\.com|huggingface\.co)/[^\s]+', link)
            extracted_links.extend(found_links)
        return extracted_links

class UseCaseGenerationAgent:
    def __init__(self, api_key):
        self.api_key = api_key
        self.llm = ChatGroq(model="mixtral-8x7b-32768", temperature=0.5, api_key=self.api_key)

    def generate_use_cases(self, company_name, extracted_links):
        """Generates use cases for leveraging AI technologies based on the specified company or industry."""
        
        prompt = f"""
        Generate use cases for leveraging AI and Generative AI technologies in the given industry or for the company {company_name}.
        Format the output as follows:

        Use Case [Number]: [Title]
        Objective/Use Case: [Brief description of the objective or use case]
        AI Application: [Description of how AI will be applied in this use case]
        Cross-Functional Benefit:
        - [Department/Function 1]: [Benefit description]
        - [Department/Function 2]: [Benefit description]
        Reference Links: 
        - Kaggle/GitHub/Hugging Face Dataset: {extracted_links[0] if extracted_links else 'N/A'}

        Search the Reference link in Kaggle, GitHub, or Hugging Face.
        """

        response = self.llm.invoke(prompt)
        
        return response.content if hasattr(response, 'content') else str(response)

def save_extracted_links_to_file(extracted_links, filename='extracted_links.txt'):
    """Saves extracted Kaggle, GitHub, and Hugging Face links to a text file."""
    with open(filename, 'w') as file:
        for link in extracted_links:
            file.write(link + '\n')

# Streamlit application layout
st.title("Industry Research and Use Case Generator")

# Input for company name and API keys
company_name = st.text_input("Enter Company Name:", "ABC Health Solutions")
industry_api_key = st.text_input("Enter Industry Research API Key:", type="password")
use_case_api_key = st.text_input("Enter Use Case Generation API Key:", type="password")

if st.button("Generate Use Cases"):
    # Initialize agents with their respective API keys
    industry_agent = IndustryResearchAgent(industry_api_key)
    link_agent = LinkExtractionAgent()
    use_case_agent = UseCaseGenerationAgent(use_case_api_key)

    # Step 1: Research the industry or company
    industry_data = industry_agent.research(company_name)

    if industry_data is not None:
        # Step 2: Extract relevant information (industry info)
        reference_links = [
            "Kaggle Dataset for Predictive Maintenance: https://www.kaggle.com/datasets/shivamb/machine-predictive-maintenance-classification",
            "GitHub Repository for Data Analysis: https://github.com/user/repo",
            "Hugging Face Model Hub: https://huggingface.co/models",
        ]

        # Step 3: Extract links from reference links
        extracted_links = link_agent.extract_links(reference_links)

        # Step 4: Save extracted links to a text file (optional)
        save_extracted_links_to_file(extracted_links)

        # Step 5: Generate use cases based on the company name and extracted links
        use_cases_response = use_case_agent.generate_use_cases(company_name, extracted_links)

        # Displaying both outputs in a formatted way
        st.subheader("Industry Research Output:")
        
        # Displaying industry data in a formatted way
        if "organic" in industry_data:
            for result in industry_data["organic"]:
                title = result.get("title", "No Title")
                snippet = result.get("snippet", "No Snippet")
                st.markdown(f"### {title}")
                st.write(snippet)
                st.write("---")

        st.subheader("Generated Use Cases:")
        
        # Process and display generated use cases beautifully
        if use_cases_response:
            use_cases_list = use_cases_response.split("Use Case")
            for case in use_cases_list[1:]:  # Skip the first empty entry
                case_parts = case.split("\n\n")
                if len(case_parts) >= 4:
                    title_line = case_parts[0].strip()
                    objective_line = case_parts[1].strip()
                    ai_application_line = case_parts[2].strip()
                    benefits_line = case_parts[3].strip()

                    # Display each part of the use case with formatting
                    st.markdown(f"#### {title_line}")
                    st.markdown(objective_line.replace("Objective/Use Case:", "### Objective/Use Case:"))
                    st.markdown(ai_application_line.replace("AI Application:", "### AI Application:"))
                    st.markdown(benefits_line.replace("Cross-Functional Benefit:", "### Cross-Functional Benefit:"))
                    st.write("---")  # Separator between use cases

    else:
        st.error("Failed to retrieve industry data.")
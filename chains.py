import os
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException

class Chain:
    def __init__(self, api_key):
        # Initialize with the API key passed as argument
        self.llm = ChatGroq(temperature=0, groq_api_key=api_key, model_name="llama-3.1-70b-versatile")

    def extract_jobs(self, cleaned_text):
        # Hardcoded prompt for extracting jobs from the webpage
        prompt_extract = PromptTemplate.from_template(
            """
            ### SCRAPED TEXT FROM WEBSITE:
            {page_data}
            ### INSTRUCTION:
            The scraped text is from the career's page of a website.
            Your job is to extract the job postings and return them in JSON format containing the following keys: `role`, `experience`, `skills` and `description`.
            Only return the valid JSON.
            ### VALID JSON (NO PREAMBLE):
            """
        )
        chain_extract = prompt_extract | self.llm
        res = chain_extract.invoke(input={"page_data": cleaned_text})
        try:
            json_parser = JsonOutputParser()
            res = json_parser.parse(res.content)
        except OutputParserException:
            raise OutputParserException("Context too big. Unable to parse jobs.")
        return res if isinstance(res, list) else [res]

    def write_mail(self, job, links, custom_email_prompt_instruction):
        # Create the prompt using the user's input for the custom instruction
        full_email_prompt = f"""
        ### JOB DESCRIPTION:
        {{job_description}}

        ### INSTRUCTION:
        {custom_email_prompt_instruction}
        Also add the most relevant ones from the following links to showcase my portfolios: {{link_list}}
        Remember you are Mohan, student of IIT Roorkee. 
        Do not provide a preamble.
        ### EMAIL (NO PREAMBLE):
        """
        prompt_email = PromptTemplate.from_template(full_email_prompt)

        chain_email = prompt_email | self.llm
        res = chain_email.invoke({"job_description": str(job), "link_list": links})
        return res.content

if __name__ == "__main__":
    # Test with an API key passed directly without using environment variables
    api_key = os.getenv("GROQ_API_KEY")  # Pass the API key here
    chain = Chain(api_key)
    print(chain.llm.groq_api_key)  # To check if it's initialized correctly

import os
import subprocess
from dotenv import load_dotenv
import streamlit as st

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

st.title("AI Resume Tailor")

with open("resume_template.tex", "r", encoding="utf-8") as f:
    latex_template = f.read()

resume_content = st.text_area(
    "Paste Existing Resume Content",
    height=300
)

jd = st.text_area(
    "Paste Job Description",
    height=300
)

if st.button("Generate Resume"):

    llm = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0.2
    )

    prompt = ChatPromptTemplate.from_template("""
You are an ATS resume optimization assistant.

STRICT RULES:
- Return ONLY optimized resume content.
- Do NOT add explanations.
- Do NOT add notes.
- Do NOT add markdown.
- Do NOT add ATS optimization comments.
- Do NOT add fake experience.
- Keep original meaning.
- Keep formatting placeholders untouched.
- Improve ATS keywords according to JD.

RESUME:
{resume}

JOB DESCRIPTION:
{jd}
""")

    chain = prompt | llm | StrOutputParser()

    optimized_content = chain.invoke({
        "resume": resume_content,
        "jd": jd
    })

    # Inject content into LaTeX
    final_tex = latex_template.replace(
        "{{PROJECTS}}",
        optimized_content
    )

    os.makedirs("output", exist_ok=True)

    tex_path = "output/tailored_resume.tex"

    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(final_tex)

    # Generate PDF using pdflatex
    subprocess.run([
        "pdflatex",
        "-output-directory=output",
        tex_path
    ])

    pdf_path = "output/tailored_resume.pdf"

    # Generate DOCX using pandoc
    subprocess.run([
        "pandoc",
        tex_path,
        "-o",
        "output/tailored_resume.docx"
    ])

    st.success("Resume Generated!")

    with open(pdf_path, "rb") as f:
        st.download_button(
            "Download PDF",
            f,
            file_name="tailored_resume.pdf"
        )

    with open("output/tailored_resume.docx", "rb") as f:
        st.download_button(
            "Download DOCX",
            f,
            file_name="tailored_resume.docx"
        )
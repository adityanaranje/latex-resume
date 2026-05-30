import os
import subprocess
import tempfile
import gradio as gr
from dotenv import load_dotenv
from pypdf import PdfReader
from docx import Document

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

# Load Resume Template
with open("resume_template.tex", "r", encoding="utf-8") as f:
    latex_template = f.read()


def extract_text_from_file(file):

    if file is None:
        return ""

    file_path = file

    if file_path.endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    elif file_path.endswith(".pdf"):
        reader = PdfReader(file_path)
        text = ""

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

        return text

    elif file_path.endswith(".docx"):
        doc = Document(file_path)

        text = "\n".join(
            paragraph.text
            for paragraph in doc.paragraphs
        )

        return text

    return ""


def generate_resume(jd_text, jd_file):

    uploaded_jd = extract_text_from_file(jd_file)

    final_jd = ""

    if jd_text and jd_text.strip():
        final_jd += jd_text

    if uploaded_jd:
        final_jd += "\n\n" + uploaded_jd

    if not final_jd.strip():
        raise gr.Error(
            "Please paste a Job Description or upload a file."
        )

    llm = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0.2
    )

    prompt = ChatPromptTemplate.from_template("""
You are an ATS Resume Optimization Assistant.

Your task:
1. Analyze the job description.
2. Optimize the resume content for ATS.
3. Add relevant keywords naturally.
4. Keep all information truthful.
5. Do not invent experience.
6. Keep professional formatting.
7. Return ONLY resume content.

CURRENT RESUME:
{resume}

JOB DESCRIPTION:
{jd}
""")

    chain = prompt | llm | StrOutputParser()

    optimized_content = chain.invoke(
        {
            "resume": latex_template,
            "jd": final_jd
        }
    )

    final_tex = latex_template.replace(
        "{{PROJECTS}}",
        optimized_content
    )

    os.makedirs("output", exist_ok=True)

    tex_path = "output/tailored_resume.tex"

    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(final_tex)

    try:

        subprocess.run(
            [
                "pdflatex",
                "-interaction=nonstopmode",
                "-output-directory=output",
                tex_path
            ],
            check=True
        )

        subprocess.run(
            [
                "pandoc",
                tex_path,
                "-o",
                "output/tailored_resume.docx"
            ],
            check=True
        )

    except subprocess.CalledProcessError as e:
        raise gr.Error(
            f"Resume generation failed: {str(e)}"
        )

    pdf_path = "output/tailored_resume.pdf"
    docx_path = "output/tailored_resume.docx"

    return (
        "✅ Resume tailored successfully!",
        pdf_path,
        docx_path
    )


with gr.Blocks(
    theme=gr.themes.Soft(),
    title="AI Resume Tailor"
) as demo:

    gr.HTML(
        """
        <div style="text-align:center;padding:20px">
            <h1>🚀 AI Resume Tailor</h1>
            <p>
                Upload a Job Description or paste it below.
                Your LaTeX resume template will be optimized
                automatically for ATS.
            </p>
        </div>
        """
    )

    with gr.Row():

        with gr.Column():

            jd_text = gr.Textbox(
                label="Paste Job Description",
                lines=12,
                placeholder="""
Paste the job description here...

Example:
Looking for a Machine Learning Engineer with:
• Python
• SQL
• AWS
• GenAI
• Docker
• MLOps
"""
            )

            jd_file = gr.File(
                label="Upload JD File",
                file_types=[
                    ".pdf",
                    ".docx",
                    ".txt"
                ]
            )

            generate_btn = gr.Button(
                "✨ Generate ATS Resume",
                variant="primary",
                size="lg"
            )

    status = gr.Markdown()

    with gr.Row():

        pdf_output = gr.File(
            label="📄 Download PDF Resume"
        )

        docx_output = gr.File(
            label="📝 Download DOCX Resume"
        )

    generate_btn.click(
        fn=generate_resume,
        inputs=[
            jd_text,
            jd_file
        ],
        outputs=[
            status,
            pdf_output,
            docx_output
        ]
    )

demo.launch()

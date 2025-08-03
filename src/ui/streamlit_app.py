# src/ui/streamlit_app.py
import streamlit as st
import os
import json
import tempfile
import zipfile
from pathlib import Path
import pandas as pd
from typing import List, Dict, Any
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our custom modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processors.document_processor import DocumentProcessor
from ai_engine.test_generator import TestCaseGenerator
from exporters.excel_exporter import TestCaseExporter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="ITASSIST - Test Case Generator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main Streamlit application"""
    
    # Title and description
    st.title("🤖 ITASSIST - Intelligent Test Case Generator")
    st.markdown("**AI-powered test case generation from BFSI documents**")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key input - auto-load from environment
        default_api_key = os.getenv("OPENAI_API_KEY", "")
        api_key = st.text_input(
            "OpenAI API Key", 
            value=default_api_key,
            type="password",
            help="API key loaded from environment" if default_api_key else "Enter your OpenAI API key"
        )
        
        # Model selection
        model_option = st.selectbox(
            "AI Model",
            ["gpt-4.1-mini-2025-04-14", "gpt-4o-mini", "gpt-3.5-turbo"],
            index=0
        )
        
        # Generation options
        st.subheader("Generation Options")
        num_test_cases = st.slider("Test Cases per Story", 5, 15, 8)
        include_edge_cases = st.checkbox("Include Edge Cases", value=True)
        include_negative_cases = st.checkbox("Include Negative Cases", value=True)
        
        # Export format
        export_format = st.multiselect(
            "Export Formats",
            ["Excel", "CSV", "JSON"],
            default=["Excel"]
        )
    
    # Initialize session state
    if 'generated_test_cases' not in st.session_state:
        st.session_state.generated_test_cases = []
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["📁 Upload & Process", "🧪 Generated Test Cases", "💬 Chat Assistant"])
    
    with tab1:
        upload_and_process_tab(api_key, num_test_cases, include_edge_cases, include_negative_cases)
    
    with tab2:
        display_test_cases_tab(export_format)
    
    with tab3:
        chat_assistant_tab(api_key)

def upload_and_process_tab(api_key: str, num_test_cases: int, include_edge_cases: bool, include_negative_cases: bool):
    """File upload and processing tab"""
    
    st.header("📁 Document Upload & Processing")
    
    # File upload section
    uploaded_files = st.file_uploader(
        "Upload your documents",
        type=['docx', 'pdf', 'xlsx', 'png', 'jpg', 'jpeg', 'tiff', 'bmp', 'txt', 'eml', 'json', 'xml', 'csv', 'zip'],
        accept_multiple_files=True,
        help="Supported formats: DOCX, PDF, XLSX, Images (PNG/JPG/TIFF/BMP), TXT, EML, JSON, XML, CSV, ZIP"
    )
    
    # Display file validation info
    if uploaded_files:
        st.info(f"📁 {len(uploaded_files)} file(s) uploaded successfully")
        
        # Show file details
        with st.expander("📋 File Details"):
            for file in uploaded_files:
                file_size = len(file.getvalue()) / (1024*1024)  # MB
                st.write(f"• **{file.name}** ({file_size:.1f} MB)")
                
                # Validate file size
                if file_size > 50:
                    st.warning(f"⚠️ {file.name} is large ({file_size:.1f} MB). Processing may take longer.")
    
    # Enhanced processing options
    st.subheader("🔧 Processing Options")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        process_embedded_content = st.checkbox("📷 Process Embedded Images/Screenshots", value=True)
    with col2:
        extract_tables = st.checkbox("📊 Extract Table Content", value=True)
    with col3:
        enhance_ocr = st.checkbox("🔍 Enhanced OCR Processing", value=True)
    
    # Custom instructions with examples
    st.subheader("📝 Custom Instructions")
    
    # Predefined instruction templates
    instruction_templates = {
        "Standard": "",
        "Focus on Negative Cases": "Generate more negative test cases and error scenarios. Include boundary testing and invalid input validation.",
        "Basic Scenarios Only": "Focus on basic happy path scenarios. Minimize edge cases and complex integration tests.",
        "Comprehensive Coverage": "Generate comprehensive test coverage including positive, negative, edge cases, and integration scenarios.",
        "Security Focus": "Emphasize security testing scenarios including authentication, authorization, and data validation.",
        "Performance Testing": "Include performance-related test scenarios for high-volume and stress testing."
    }
    
    selected_template = st.selectbox("Choose Instruction Template:", list(instruction_templates.keys()))
    
    custom_instructions = st.text_area(
        "Custom Instructions",
        value=instruction_templates[selected_template],
        placeholder="e.g., 'Focus on payment validation scenarios' or 'Create 4 test cases per acceptance criteria'",
        help="Provide specific instructions to customize test case generation"
    )
    
    # Process button
    if st.button("🚀 Generate Test Cases", type="primary", disabled=not api_key or not uploaded_files):
        if not api_key:
            st.error("Please provide OpenAI API key in the sidebar")
            return
        
        if not uploaded_files:
            st.error("Please upload at least one document")
            return
        
        process_files(uploaded_files, api_key, custom_instructions, num_test_cases, 
                     include_edge_cases, include_negative_cases, process_embedded_content)

def process_files(uploaded_files, api_key: str, custom_instructions: str, 
                 num_test_cases: int, include_edge_cases: bool, include_negative_cases: bool,
                 process_embedded_content: bool):
    """Process uploaded files and generate test cases"""
    
    # Initialize processors
    doc_processor = DocumentProcessor()
    test_generator = TestCaseGenerator(api_key)
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        all_content = []
        total_files = len(uploaded_files)
        
        # Process each file
        for i, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Processing {uploaded_file.name}...")
            progress_bar.progress((i + 1) / (total_files + 2))
            
            # Handle ZIP files
            if uploaded_file.name.endswith('.zip'):
                extracted_content = process_zip_file(uploaded_file, doc_processor)
                all_content.extend(extracted_content)
            else:
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                
                # Process the file
                result = doc_processor.process_file(tmp_file_path)
                all_content.append(result)
                
                # Clean up temporary file
                os.unlink(tmp_file_path)
        
        # Combine all extracted content
        status_text.text("Combining extracted content...")
        progress_bar.progress(0.9)
        
        combined_content = combine_extracted_content(all_content)
        
        # Generate custom instructions
        generation_instructions = build_generation_instructions(
            custom_instructions, num_test_cases, include_edge_cases, include_negative_cases
        )
        
        # Generate test cases
        status_text.text("Generating test cases with AI...")
        progress_bar.progress(0.95)
        
        test_cases = test_generator.generate_test_cases(combined_content, generation_instructions)
        
        if test_cases:
            st.session_state.generated_test_cases = test_cases
            st.session_state.processing_complete = True
            
            progress_bar.progress(1.0)
            status_text.text("✅ Processing complete!")
            
            # Display summary
            st.success(f"Successfully generated {len(test_cases)} test cases!")
            
            # Show content preview
            with st.expander("📄 Extracted Content Preview"):
                st.text(combined_content[:1000] + "..." if len(combined_content) > 1000 else combined_content)
                
        else:
            st.error("No test cases could be generated. Please check your documents and try again.")
            
    except Exception as e:
        st.error(f"Error during processing: {str(e)}")
        logger.error(f"Processing error: {str(e)}")

def process_zip_file(zip_file, doc_processor: DocumentProcessor) -> List[Dict]:
    """Process files within a ZIP archive"""
    extracted_content = []
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Extract ZIP file
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Process each extracted file
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if Path(file_path).suffix.lower() in doc_processor.supported_formats:
                    result = doc_processor.process_file(file_path)
                    extracted_content.append(result)
    
    return extracted_content

def combine_extracted_content(content_list: List[Dict]) -> str:
    """Combine content from multiple files"""
    combined_text = []
    
    for content in content_list:
        if content.get('content'):
            file_info = f"\n--- Content from {content.get('file_name', 'Unknown')} ---\n"
            combined_text.append(file_info + content['content'])
        
        # Add table content if available
        if content.get('tables'):
            combined_text.append("\nTables:\n" + '\n'.join(content['tables']))
        
        # Add OCR text from images
        if content.get('image_text'):
            combined_text.append("\nImage Text:\n" + '\n'.join(content['image_text']))
    
    return '\n\n'.join(combined_text)

def build_generation_instructions(custom_instructions: str, num_test_cases: int, 
                                include_edge_cases: bool, include_negative_cases: bool) -> str:
    """Build generation instructions based on user preferences"""
    instructions = []
    
    if custom_instructions:
        instructions.append(custom_instructions)
    
    instructions.append(f"Generate exactly {num_test_cases} test cases per user story/requirement")
    
    if include_edge_cases:
        instructions.append("Include edge cases and boundary conditions")
    
    if include_negative_cases:
        instructions.append("Include negative test scenarios and error conditions")
    
    instructions.append("Focus on BFSI domain scenarios with realistic banking data")
    
    return ". ".join(instructions)

def display_test_cases_tab(export_formats: List[str]):
    """Display generated test cases"""
    
    st.header("🧪 Generated Test Cases")
    
    if not st.session_state.generated_test_cases:
        st.info("No test cases generated yet. Please upload documents and process them first.")
        return
    
    test_cases = st.session_state.generated_test_cases
    
    # Display summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Test Cases", len(test_cases))
    with col2:
        high_priority = len([tc for tc in test_cases if tc.get("Priority") == "High"])
        st.metric("High Priority", high_priority)
    with col3:
        regression_tests = len([tc for tc in test_cases if tc.get("Part of Regression") == "Yes"])
        st.metric("Regression Tests", regression_tests)
    with col4:
        unique_stories = len(set(tc.get("User Story ID", "") for tc in test_cases))
        st.metric("User Stories", unique_stories)
    
    # Filter options
    with st.expander("🔍 Filter Test Cases"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            priority_filter = st.multiselect(
                "Priority", 
                ["High", "Medium", "Low"],
                default=["High", "Medium", "Low"]
            )
        
        with col2:
            regression_filter = st.multiselect(
                "Regression", 
                ["Yes", "No"],
                default=["Yes", "No"]
            )
        
        with col3:
            story_ids = list(set(tc.get("User Story ID", "") for tc in test_cases))
            story_filter = st.multiselect(
                "User Story ID",
                story_ids,
                default=story_ids
            )
    
    # Apply filters
    filtered_test_cases = [
        tc for tc in test_cases
        if (tc.get("Priority") in priority_filter and
            tc.get("Part of Regression") in regression_filter and
            tc.get("User Story ID") in story_filter)
    ]
    
    # Display test cases table
    if filtered_test_cases:
        st.subheader(f"Test Cases ({len(filtered_test_cases)} of {len(test_cases)})")
        
        # Convert to DataFrame for display
        df = pd.DataFrame(filtered_test_cases)
        
        # Configure column display
        column_config = {
            "Steps": st.column_config.TextColumn(width="large"),
            "Test Case Description": st.column_config.TextColumn(width="medium"),
            "Expected Result": st.column_config.TextColumn(width="medium"),
        }
        
        st.dataframe(
            df,
            use_container_width=True,
            column_config=column_config,
            hide_index=True
        )
        
        # Export section
        st.subheader("📥 Export Test Cases")
        
        col1, col2, col3 = st.columns(3)
        
        exporter = TestCaseExporter()
        
        if "Excel" in export_formats:
            with col1:
                if st.button("📊 Download Excel", type="primary"):
                    try:
                        # Create Excel in memory instead of temp file
                        import io
                        from openpyxl import Workbook
                        
                        # Use our exporter but modify to work with BytesIO
                        exporter = TestCaseExporter()
                        
                        # Create DataFrame
                        df = pd.DataFrame(filtered_test_cases)
                        
                        # Ensure all required columns exist
                        for col in exporter.required_columns:
                            if col not in df.columns:
                                df[col] = ""
                        
                        # Reorder columns
                        df = df[exporter.required_columns]
                        
                        # Create Excel file in memory
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df.to_excel(writer, sheet_name='Test Cases', index=False)
                            
                            # Get workbook and worksheet for formatting
                            workbook = writer.book
                            worksheet = writer.sheets['Test Cases']
                            
                            # Apply basic formatting
                            from openpyxl.styles import Font, PatternFill
                            
                            # Header formatting
                            for cell in worksheet[1]:
                                cell.font = Font(bold=True, color="FFFFFF")
                                cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
                        
                        output.seek(0)
                        
                        st.download_button(
                            label="📊 Download Excel File",
                            data=output.getvalue(),
                            file_name=f"test_cases_{len(filtered_test_cases)}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                        
                    except Exception as e:
                        st.error(f"Export error: {str(e)}")
                        logger.error(f"Excel export error: {str(e)}")
        
        if "CSV" in export_formats:
            with col2:
                if st.button("📄 Download CSV"):
                    try:
                        csv_data = pd.DataFrame(filtered_test_cases).to_csv(index=False)
                        st.download_button(
                            label="📄 Download CSV File",
                            data=csv_data,
                            file_name=f"test_cases_{len(filtered_test_cases)}.csv",
                            mime="text/csv"
                        )
                    except Exception as e:
                        st.error(f"Export error: {str(e)}")
        
        if "JSON" in export_formats:
            with col3:
                if st.button("🔧 Download JSON"):
                    try:
                        json_data = json.dumps(filtered_test_cases, indent=2, ensure_ascii=False)
                        st.download_button(
                            label="🔧 Download JSON File",
                            data=json_data,
                            file_name=f"test_cases_{len(filtered_test_cases)}.json",
                            mime="application/json"
                        )
                    except Exception as e:
                        st.error(f"Export error: {str(e)}")
    
    else:
        st.warning("No test cases match the selected filters.")

def chat_assistant_tab(api_key: str):
    """Chat assistant for test case customization"""
    
    st.header("💬 Chat Assistant")
    st.markdown("Ask questions about your test cases or request modifications")
    
    if not api_key:
        st.warning("Please provide OpenAI API key to enable chat functionality")
        return
    
    if not st.session_state.generated_test_cases:
        st.info("Generate test cases first to enable chat assistance")
        return
    
    # Chat interface
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    
    # Display chat history
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about your test cases..."):
        # Add user message
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = generate_chat_response(prompt, st.session_state.generated_test_cases, api_key)
                st.markdown(response)
        
        # Add assistant message
        st.session_state.chat_messages.append({"role": "assistant", "content": response})

def generate_chat_response(prompt: str, test_cases: List[Dict], api_key: str) -> str:
    """Generate chat response about test cases"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        # Prepare context
        test_cases_summary = f"Total test cases: {len(test_cases)}\n"
        test_cases_summary += "Sample test cases:\n"
        for i, tc in enumerate(test_cases[:3], 1):
            test_cases_summary += f"{i}. {tc.get('Test Case Description', '')}\n"
        
        chat_prompt = f"""
        You are an expert BFSI test engineer assistant. Answer questions about the generated test cases.
        
        Test Cases Context:
        {test_cases_summary}
        
        User Question: {prompt}
        
        Provide helpful, specific answers about the test cases. If asked to modify test cases, 
        provide specific suggestions or instructions.
        """
        
        response = client.chat.completions.create(
            model="gpt-4.1-mini-2025-04-14",
            messages=[
                {"role": "system", "content": "You are a helpful BFSI testing expert."},
                {"role": "user", "content": chat_prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}"

if __name__ == "__main__":
    main()
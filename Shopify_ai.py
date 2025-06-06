import streamlit as st
import streamlit as st
import requests
import json
import os
import io
import sys
import re
from datetime import datetime, timedelta
import ast
import time
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


st.set_page_config(page_title="🛍️ Agentic AI for Shopify – Built by Rishabh Shah", layout="wide")
st.title("🛍️ Agentic AI for Shopify – Built by Rishabh Shah")

tab1, tab2 ,tab3= st.tabs(["📊 Analytics With Code","🧠 AI Agent Chat","🗣️ Ask Anything (AI)"])

with tab1:
    # Your current chat code here
    st.subheader("Ask Shopify Analytics questions")
    # === Session State Init ===
    if "chat_history_tab1" not in st.session_state:
        st.session_state.chat_history_tab1 = []
    if "input_text" not in st.session_state:
        st.session_state.input_text = ""
    if "api_call" not in st.session_state:
        st.session_state.api_call = 1
    if "shop_tab1" not in st.session_state:
        st.session_state.shop_tab1 = ""
    if "token_tab1" not in st.session_state:
        st.session_state.token_tab1 = ""

    # === Function: Call AI Agent and Execute Shopify Code ===
    def handle_send_tab1():
        user_query = st.session_state.input_text.strip()
        if not user_query:
            return
        # Set default SHOP and ACCESS_TOKEN if not provided
        if not st.session_state.shop_tab1 or not st.session_state.token_tab1:
            st.session_state.chat_history_tab1.append({
                "sender": "🤖AI Bot",
                "content": "⚠️ Please enter both SHOP and ACCESS_TOKEN above."
            })
            return
        # 🔐 Ensure valid domain
        if not st.session_state.shop_tab1.endswith(".myshopify.com"):
            st.session_state.shop_tab1 += ".myshopify.com"


        st.session_state.chat_history_tab1.append({"sender": "🙋You", "content": user_query})
        time.sleep(5)

        question = f"""
        SHOP = os.getenv("SHOP", "{st.session_state.shop_tab1}")
        ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", "{st.session_state.token_tab1}")

        You are a Python coding agent that generates clean, production-ready Python code using the `requests` library to call the Shopify Graphql admin API (2024-04).

        #######################
        # === GENERAL RULES ===
        #######################
        - Use SHOP and ACCESS_TOKEN as variables (do not hardcode).
        - Always include headers with `X-Shopify-Access-Token`.
        - Safely handle missing or empty fields using `.get()`.
        - Avoid IndexError by validating list length and types before accessing elements.
        - Always use the **latest valid Shopify Admin API version (2024-04)**.
        - **Avoid deprecated fields or endpoints**. If a GraphQL field or REST endpoint has been removed, skip or replace it with a supported alternative.
        - When uncertain about field availability in GraphQL, **prefer REST** if the data is critical and available there.

        
        #########################
        # === CUSTOM SCENARIOS ===
        #########################

        # 1. Customers who have not ordered
        - If the prompt asks for customers who have not ordered (by id, email, or name):
            - Collect them in a list named `churned_customers`.
            - Format each entry in the list based on the `output_format` variable:
                - "id": return customer ID.
                - "email": return email if available, else fallback to full name.
                - "name": return full name by combining first and last names.
            - Implement helper functions:
                - `get_customers()` — fetch all customers.
                - `get_orders(customer_id)` — fetch orders by customer.
            - Ensure `get_orders()` returns an empty list if the API response is missing or malformed.
            - Parse dates using `datetime.strptime(...).replace(tzinfo=None)`.

        # 2. List churned customers
        - If the prompt requests churned customers:
            - Return a dictionary with:
                - `"churned_customers_count"`
                - `"churned_customers"` formatted using `output_format`.
        
        
        # 3. Store churn rate in % only
        - If the prompt asks for churn rate (e.g., "store's churn rate", "churn %"):
            - Return a dictionary with:
                - `"churn_rate_percent"`: a percentage string formatted to 2 decimal places, e.g. `"64.69%"`.
            - Do not include any other output.



        # 4. Average Order Value (AOV) of repeat customers
        - If the prompt asks for AOV:
            - A repeat customer has more than one order.
            - Convert numeric strings like `total_price` to float.
            - Compute average order value across all repeat customers.
            - Return:
                - `"average_order_value"`: formatted with 2 decimal places and `$` symbol (e.g. `"52.43$"`).

        # 5. Abandoned checkouts
        - If the prompt mentions abandoned checkouts:
            - Use `/admin/api/2023-10/checkouts.json`.

            - If the prompt implies abandoned **products** (e.g., "products abandoned", "items left in cart"):
                - Extract product IDs from `line_items` in each checkout.
                - Return:
                    - `"abandoned_checkouts_count"`
                    - `"abandoned_products"` list.
                        - If the prompt implies abandoned **customers** (e.g., "customers abandoned", "users abandoned checkout"):
            
            - Identify customers who started but didn’t complete checkout.
                - Return:
                    - `"abandoned_checkouts_count"`
                    - `"abandoned_customers"` formatted by `output_format`.

            - If ambiguous, default to customer-based abandonment.

        # 6. Product sales by revenue (lowest-selling or most-selling or top products)
        - Set the date range for orders as:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")  # One year ago
            end_date = datetime.now().strftime("%Y-%m-%d")                             # Today

        - Fetch orders with query filter: `created_at:>=start_date created_at:<=end_date`.

        - For each order, retrieve `lineItems(first: 100)`.

        - For each line item, extract:
            - `title` (string)
            - `quantity` (integer)
            - `originalUnitPriceSet.shopMoney.amount` (string, convert to float)
            - `product.id` (string)

        - Aggregate by `product.id`:
            - total revenue = quantity * unit price
            - keep latest seen `unit_price` and `title`

        - Sort by:
            - If prompt contains "top", "most", "highest" → sort by `total_revenue` descending
            - If prompt contains "lowest", "least", "bottom" → sort by `total_revenue` ascending

        - Limit results using a number in the prompt (default: 10)

        - If the prompt includes **"price"** and "title" or "name", return:
            - list of `{{"product_title": ..., "unit_price": ...}}`

        - Otherwise, return:
            - list of `{{"product_title": ..., "total_revenue": ...}}`

        ##############################
        # === OUTPUT REQUIREMENTS ===
        ##############################
        - Assign the final result to a variable named `final_output`.
        - Only return valid, clean Python code (no markdown, no explanations).
        - The last line **must be**:
            print(final_output)

        Prompt: {user_query}
        """
        url = "https://api.indiaagi.ai/test/sse"
        params = {
            "question": question,
            "rounds": 1,
            "model": "OpenAI"
        }
        clean_code = ""
        try:
            with requests.get(url, params=params, stream=True, verify=False) as response:
                response.raise_for_status()
                buffer = {}
                for line in response.iter_lines(decode_unicode=True):
                    if not line:
                        if buffer.get("id") == "2":
                            data_json = buffer.get("data")
                            if data_json:
                                data_obj = json.loads(data_json)
                                code = data_obj.get("response")
                                # Clean code block formatting
                                code = re.sub(r"^```python\\n|\\n```$", "", code.strip())  # Remove ```python ... ```
                                code = code.encode('utf-8').decode('utf-8-sig')            # Remove BOM
                                code = code.replace("\\n", "\n")                           # Convert \n to real newlines
                                                                                                                                                                                                    
                                # Replace env vars with actual values
                                code = re.sub(r'SHOP\s*=\s*os.getenv\([\'"].+?[\'"]\)', f'SHOP = "{st.session_state.shop_tab1}"', code)
                                code = re.sub(r'ACCESS_TOKEN\s*=\s*os.getenv\([\'"].+?[\'"]\)', f'ACCESS_TOKEN = "{st.session_state.token_tab1}"', code)
                                clean_code = code.replace("python","").replace("```","").strip()
                                # st.code(clean_code, language="python")
                                with st.expander("Show Code"):
                                    st.code(clean_code, language="python")
                                print(repr(clean_code))
                                break
                        buffer = {}
                        continue
                    if line.startswith("id:"):
                        buffer["id"] = line[len("id:"):].strip()
                    elif line.startswith("data:"):
                        buffer["data"] = line[len("data:"):].strip()
        except Exception as e:
            st.session_state.chat_history_tab1.append({"sender": "🤖AI Bot", "content": f"❌ API error: {str(e)}"})
            return

        # Execute the clean Python code and capture output
        try:
            output_buffer = io.StringIO()
            sys_stdout_backup = sys.stdout
            sys.stdout = output_buffer

            os.environ["SHOP"] = st.session_state.shop_tab1
            os.environ["ACCESS_TOKEN"] = st.session_state.token_tab1

            exec_globals = {
                "__builtins__": __builtins__,
                "os": os,
                "requests": requests,
                "datetime": datetime,
                "timedelta": timedelta
            }
            exec(clean_code, exec_globals)

            sys.stdout = sys_stdout_backup
            final_output = output_buffer.getvalue().strip()

            if final_output:
                try:
                    parsed = json.loads(final_output)
                except json.JSONDecodeError:
                    try:
                        parsed = ast.literal_eval(final_output)
                    except Exception:
                        parsed = final_output
            else:
                st.session_state.chat_history_tab1.append({"sender": "🤖AI Bot", "content": "❌ Empty output from executed code."})
                return

            # Beautify output
            if isinstance(parsed, list):
                beautified = "\n".join(
                    f"- **{item.get('title', str(item))}** — ₹{item.get('price', '')}"
                    if isinstance(item, dict) else f"- {item}"
                    for item in parsed
                )
            elif isinstance(parsed, dict) and all(isinstance(k, str) and isinstance(v, int) for k, v in parsed.items()):
                sorted_items = sorted(parsed.items(), key=lambda x: x[1], reverse=True)
                beautified = "\n".join(f"- **{k}** → {v} purchases" for k, v in sorted_items)
            else:
                beautified = str(parsed)

            st.session_state.chat_history_tab1.append({"sender": "🤖AI Bot", "content": beautified})
        except Exception as e:
            # sys.stdout = sys_stdout_backup
            # if "Failed to resolve" in str(e) and st.session_state.api_call < 3:
            #     st.session_state.api_call += 1
            #     handle_send_tab1()
            #     return
            # else:
            #     st.session_state.chat_history.append({"sender": "AI Bot", "content": f"❌ Code execution error: {str(e)}"})
            sys.stdout = sys_stdout_backup
            # Initialize retry count if not already done
            if 'api_call' not in st.session_state:
                st.session_state.api_call = 0

            # Retry logic: try up to 3 times
            if st.session_state.api_call < 3:
                st.session_state.api_call += 1
                handle_send_tab1()  # Retry
                return
            else:
                st.session_state.chat_history_tab1.append({
                    "sender": "🤖AI Bot",
                    "content": f"❌ Code execution error after 3 retries: {str(e)}"
                })
                st.session_state.api_call = 0  # reset if needed

        st.session_state.input_text = ""

    # === Function: Clear Chat ===
    def clear_chat_tab1():
        st.session_state.chat_history_tab1 = []
        st.session_state.input_text = ""
        st.session_state.api_call = 1

    # === UI Layout ===
    # Manual SHOP + TOKEN inputs
    st.button("🧹 Clear Chat", key="clear_btn_tab1", on_click=clear_chat_tab1)
    st.text_input("🛒 Shopify Store Name (e.g., qeapptest.myshopify.com):", key="shop_tab1")
    st.text_input("🔐 Access Token:", type="password", key="token_tab1")

    
    predefined_questions = [
    "Show customers who have not ordered",
    "What is the store's churn rate?",
    "List churned customers",
    "Average order value of repeat customers",
    "Show abandoned checkouts",
    "Show lowest-selling products last month"
    ]

    cols = st.columns(len(predefined_questions))  # create one column per question

    for idx, question in enumerate(predefined_questions):
        if cols[idx].button(question):
            st.session_state.input_text = question
    
    # Chat History Display
    for message in st.session_state.chat_history_tab1:
        st.markdown(f"**{message['sender']}**: {message['content']}")

    # Input & Buttons
    st.text_input("🙋You:", key="input_text", placeholder="Ask about orders, customers, products, etc...")
    st.button("Send", key="send_btn_tab1", on_click=handle_send_tab1)

with tab2:
    st.subheader("Ask Shopify-related questions to know details in text format")
    # Use separate session state variables for tab2 if needed
    if "chat_history_tab2" not in st.session_state:
        st.session_state.chat_history_tab2 = []
    if "input_text_tab2" not in st.session_state:
        st.session_state.input_text_tab2 = ""
    if "shop_tab2" not in st.session_state:
        st.session_state.shop_tab2 = ""
    if "token_tab2" not in st.session_state:
        st.session_state.token_tab2 = ""

    def handle_send_tab2():
        user_query = st.session_state.input_text_tab2.strip()
        if not user_query:
            return
        if not st.session_state.shop_tab2 or not st.session_state.token_tab2:
            st.session_state.chat_history_tab2.append({
                "sender": "🤖AI Bot",
                "content": "⚠️ Please enter both SHOP and ACCESS_TOKEN above."
            })
            return
        if not st.session_state.shop_tab2.endswith(".myshopify.com"):
            st.session_state.shop_tab2 += ".myshopify.com"

        st.session_state.chat_history_tab2.append({"sender": "🙋You", "content": user_query})
        time.sleep(5)
        
        question = f"""
        Prompt: {user_query}
        Following details are provided related to Shopify store:
        - SHOP: {st.session_state.shop_tab2}
        - ACCESS_TOKEN: {st.session_state.token_tab2}
        """

        url = "https://api.indiaagi.ai/test/sse"
        params = {
            "question": question,
            "rounds": 1,
            "model": "OpenAI"
        }
        try:
            with requests.get(url, params=params, stream=True, verify=False) as response:
                response.raise_for_status()
                buffer = {}
                for line in response.iter_lines(decode_unicode=True):
                    if not line:
                        if buffer.get("id") == "2":
                            data_json = buffer.get("data")
                            if data_json:
                                try:
                                    data_json = data_json.encode('utf-8', 'replace').decode()
                                    data_obj = json.loads(data_json)
                                    print("Parsed data_obj:", data_obj)

                                    response_type = data_obj.get("type")

                                    if response_type == "TextResponse":
                                        response = data_obj.get("response")

                                    elif response_type == "InternetSearch":
                                        search = data_obj.get("internetSearch", {})
                                        response = f"Search Query: {search.get('searchQuery')}\n\n"
                                        for item in search.get("searchResponse", []):
                                            title = item.get("title")
                                            link = item.get("link")
                                            snippet = item.get("snippet")
                                            response += f"- [{title}]({link}): {snippet}\n"

                                    else:
                                        response = "⚠️ Unknown response type."

                                    print("Final response to show:", response)

                                    st.session_state.chat_history_tab2.append({
                                        "sender": "🤖AI Bot",
                                        "content": response
                                    })

                                except json.JSONDecodeError as e:
                                    print("JSON decode error:", e)
                            else:
                                print("data_json is None or empty")    

                        buffer = {}
                        continue

                    if line.startswith("id:"):
                        buffer["id"] = line[len("id:"):].strip()
                    elif line.startswith("data:"):
                        buffer["data"] = line[len("data:"):].strip()

        except Exception as e:
            st.session_state.chat_history_tab2.append({"sender": "🤖AI Bot", "content": f"❌ API error: {str(e)}"})

        st.session_state.input_text_tab2 = ""

    def clear_chat_tab2():
        st.session_state.chat_history_tab2 = []
        st.session_state.input_text_tab2 = ""

    st.button("🧹 Clear Chat", key="clear_btn_tab2", on_click=clear_chat_tab2)
    # Unique keys here to avoid conflict with tab1
    st.text_input("🛒 Shopify Store Name (e.g., qeapptest.myshopify.com):", key="shop_tab2")
    st.text_input("🔐 Access Token:", type="password", key="token_tab2")
    
    
    predefined_questions = [
    "What is our total revenue this month?",
    "What is our average order value (AOV)?",
    "What are our daily/weekly/monthly sales trends?",
    "What are the top 5 best-selling products?",
    "What is the revenue breakdown by product category?",
    "What are our gross profit margins by product?",
    "What percentage of revenue comes from repeat customers?",
    ]

    cols = st.columns(len(predefined_questions))  # create one column per question

    for idx, question in enumerate(predefined_questions):
        if cols[idx].button(question):
            st.session_state.input_text_tab2 = question
    
    
    for message in st.session_state.chat_history_tab2:
        st.markdown(f"**{message['sender']}**: {message['content']}")

    st.text_input("🙋You:", key="input_text_tab2", placeholder="Ask about orders, customers, products, etc...")
    st.button("Send", key="send_btn_tab2", on_click=handle_send_tab2)
    
with tab3:
    st.subheader("🗣️ Ask Anything (AI) – General AI Chat Assistant")

    if "chat_history_tab3" not in st.session_state:
        st.session_state.chat_history_tab3 = []
    if "input_text_tab3" not in st.session_state:
        st.session_state.input_text_tab3 = ""

    def handle_send_tab3():
        user_query = st.session_state.input_text_tab3.strip()
        if not user_query:
            return

        st.session_state.chat_history_tab3.append({"sender": "🙋You", "content": user_query})
        time.sleep(2)

        question = f"""Prompt: {user_query}"""

        url = "https://api.indiaagi.ai/test/sse"
        params = {
            "question": question,
            "rounds": 1,
            "model": "OpenAI"
        }

        try:
            with requests.get(url, params=params, stream=True, verify=False) as response:
                response.raise_for_status()
                buffer = {}
                for line in response.iter_lines(decode_unicode=True):
                    if not line:
                        if buffer.get("id") == "2":
                            data_json = buffer.get("data")
                            if data_json:
                                try:
                                    data_json = data_json.encode('utf-8', 'replace').decode()
                                    data_obj = json.loads(data_json)

                                    response_type = data_obj.get("type")
                                    if response_type == "TextResponse":
                                        response = data_obj.get("response")
                                    elif response_type == "InternetSearch":
                                        search = data_obj.get("internetSearch", {})
                                        response = f"Search Query: {search.get('searchQuery')}\n\n"
                                        for item in search.get("searchResponse", []):
                                            title = item.get("title")
                                            link = item.get("link")
                                            snippet = item.get("snippet")
                                            response += f"- [{title}]({link}): {snippet}\n"
                                    else:
                                        response = "⚠️ Unknown response type."

                                    st.session_state.chat_history_tab3.append({
                                        "sender": "🤖AI Bot",
                                        "content": response
                                    })

                                except json.JSONDecodeError as e:
                                    print("JSON decode error:", e)
                            else:
                                print("data_json is None or empty")
                        buffer = {}
                        continue

                    if line.startswith("id:"):
                        buffer["id"] = line[len("id:"):].strip()
                    elif line.startswith("data:"):
                        buffer["data"] = line[len("data:"):].strip()

        except Exception as e:
            st.session_state.chat_history_tab3.append({"sender": "🤖AI Bot", "content": f"❌ API error: {str(e)}"})

        st.session_state.input_text_tab3 = ""

    def clear_chat_tab3():
        st.session_state.chat_history_tab3 = []
        st.session_state.input_text_tab3 = ""

    st.button("🧹 Clear Chat", key="clear_btn_tab3", on_click=clear_chat_tab3)

    # Predefined general-purpose AI questions
    predefined_questions = [
        "How can I reduce cart abandonment on my website?",
        "What are good KPIs for an eCommerce store?",
        "Give me a SWOT analysis template.",
        "Suggest 3 ideas to improve customer retention.",
        "What are the latest trends in eCommerce?",
        "Explain how inflation affects small businesses.",
    ]

    cols = st.columns(len(predefined_questions))
    for idx, question in enumerate(predefined_questions):
        if cols[idx].button(question, key=f"q_tab3_{idx}"):
            st.session_state.input_text_tab3 = question

    for message in st.session_state.chat_history_tab3:
        st.markdown(f"**{message['sender']}**: {message['content']}")

    st.text_input("🙋You:", key="input_text_tab3", placeholder="Ask anything (AI-powered)")
    st.button("Send", key="send_btn_tab3", on_click=handle_send_tab3)

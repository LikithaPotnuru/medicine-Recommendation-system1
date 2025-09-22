import streamlit as st
import requests

API_URL = "http://127.0.0.1:5000"

st.set_page_config(page_title="Medicine Recommendation", layout="centered")
st.title("💊 Medicine Recommendation System")

# -------------------- Session state --------------------
if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "search_done" not in st.session_state:
    st.session_state.search_done = False
if "purchase_feedbacks" not in st.session_state:
    st.session_state.purchase_feedbacks = {}

# -------------------- Inputs --------------------
username = st.text_input("Enter your username:", key="username_input")
query = st.text_input("Search medicine by name or symptom:", key="search_input")
search_pressed = st.button("🔍 Search")
st.markdown("---")

# -------------------- Helpers --------------------
def normalize_search_response(resp_json):
    return resp_json.get("results", []) if resp_json else []

def normalize_recommend_response(resp_json):
    history = resp_json.get("history", [])
    collaborative = resp_json.get("collaborative", [])
    top_meds = resp_json.get("top_meds", [])
    new_user = resp_json.get("new_user", False)
    return history, collaborative, top_meds, new_user

def display_medicines(meds, section_title, key_prefix):
    if not meds:
        st.info(f"No medicines available for {section_title}.")
        return

    st.subheader(section_title)
    for idx, med in enumerate(meds):
        med_id = med.get("id", idx)
        med_name = med.get("name", "Unknown")
        med_uses = med.get("uses", "N/A")
        med_stock = med.get("stock", 0)
        med_price = float(med.get("price", 0))

        st.markdown(f"<h3 style='color:darkblue'>{med_name}</h3>", unsafe_allow_html=True)
        st.write("Uses:", med_uses)
        st.write(f"Stock: {med_stock}")
        st.write(f"Price per unit: ₹{med_price:.2f}")

        if med_stock == 0:
            st.warning("⚠️ Out of stock. Check substitutes below.")
            try:
                r_sub = requests.get(f"{API_URL}/substitutes/{med_id}", timeout=5)
                r_sub.raise_for_status()
                subs = r_sub.json().get("substitutes", [])
                if subs:
                    display_medicines(subs, f"Substitutes for {med_name}", f"sub_{med_id}")
            except:
                st.error("Error fetching substitutes.")
            continue

        quantity_key = f"quantity_{key_prefix}_{med_id}_{idx}"
        button_key = f"purchase_{key_prefix}_{med_id}_{idx}"

        col_btn, col_qty = st.columns([3, 1])
        with col_qty:
            st.caption("Quantity")
            quantity = st.number_input(
                "", min_value=1, max_value=int(med_stock), value=1,
                key=quantity_key, step=1, label_visibility="collapsed"
            )
        with col_btn:
            if st.button("🛒 Purchase", key=button_key):
                if not username:
                    st.error("Please enter your username before purchasing.")
                else:
                    payload = {"username": username, "medicine_id": med_id, "quantity": quantity}
                    try:
                        r = requests.post(f"{API_URL}/purchase", json=payload, timeout=5)
                        rj = r.json()
                        if r.status_code == 200:
                            st.success(rj.get("message"))
                            med["stock"] = rj.get("stock", med_stock)
                        else:
                            st.error(rj.get("error", "Purchase failed."))
                    except:
                        st.error("Error calling purchase API.")

        st.info(f"Total price for {quantity} unit(s): ₹{quantity * med_price:.2f}")
        st.write("---")

# -------------------- Main Logic --------------------
if not username:
    st.warning("Please enter your username above to proceed.")
else:
    if search_pressed:
        st.session_state.search_done = True
        st.session_state.search_results = []

        if not query.strip():
            try:
                r = requests.get(f"{API_URL}/recommend/{username}", timeout=8)
                r.raise_for_status()
                rec_json = r.json()
                history, collaborative, top_meds, new_user = normalize_recommend_response(rec_json)

                display_list = []
                if history:
                    display_list.append(("📌 Your Purchase History", history, "history"))
                if collaborative:
                    display_list.append(("🤝 People like you also purchased", collaborative, "collab"))
                if top_meds:
                    display_list.append(("🔥 Top Medicines", top_meds, "top"))

                st.session_state.search_results = display_list

            except:
                st.error("Error fetching recommendations.")
        else:
            try:
                r = requests.get(f"{API_URL}/search", params={"query": query}, timeout=8)
                r.raise_for_status()
                meds = normalize_search_response(r.json())
                if meds:
                    st.success(f"Found {len(meds)} result(s) for '{query}'.")
                    st.session_state.search_results = [(f"🔍 Search Results for '{query}'", meds, "search")]
                else:
                    st.info(f"No medicines found for '{query}'.")
            except:
                st.error("Error calling search API.")

    if st.session_state.search_done and st.session_state.search_results:
        for title, meds, key_prefix in st.session_state.search_results:
            display_medicines(meds, title, key_prefix)

st.markdown("---")
st.caption("Tip: Click Search to find medicines by name or symptom. Select quantity beside the purchase button. Purchase feedback appears below.")

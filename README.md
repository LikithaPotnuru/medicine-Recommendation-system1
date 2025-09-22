# Medicine Recommendation System

## 🎯 Objective

The aim of this project is to build a **Medicine Recommendation System** that suggests suitable medicines to users based on their symptoms. The system not only recommends medicines but also provides precautions and takes into account the user’s medical history if available.

## ✅ What We Have Done (Features / Work Done)

* Preprocessed and cleaned the medicine dataset (`cleaned_medicine_data.csv`).
* Implemented a recommendation logic to map symptoms to medicines.
* Built scripts for inserting medicine data into the database (`insert_medicines.py`).
* Developed an **API layer** (`api.py`) to serve medicine recommendations programmatically.
* Created an **application interface** (`app.py`) for user interaction.
* Documented and explored the logic in `Medicine_project.ipynb`.

## ⚙️ How to Initialize & Run Everything (Setup & Usage Instructions)

### 1. Clone the Repository

```bash
git clone <your-repo-link>
cd medicine-Recommendation-system1-main
```

### 2. Create and Activate Virtual Environment

```bash
python -m venv venv
source venv/bin/activate   # On Linux/Mac
venv\Scripts\activate      # On Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Insert Medicine Data into Database (if applicable)

```bash
python insert_medicines.py
```

### 5. Run the Application

* **Option A: Run API**

```bash
python api.py
```

* **Option B: Run App**

```bash
python app.py
```

### 6. Explore Notebook (Optional)

You can also open `Medicine_project.ipynb` in Jupyter Notebook for detailed exploration and experimentation.

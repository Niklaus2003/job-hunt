import re
from bs4 import BeautifulSoup

filepath = r"C:\Users\AaronFrancis\.gemini\antigravity\brain\0e9417e1-a27a-40f9-a473-5807ad529128\browser\scratchpad_glw8cv1g.md"

with open(filepath, "r", encoding="utf-8") as f:
    html_content = f.read()

# Strip any markdown wrapper if present
if "```html" in html_content:
    html_content = html_content.split("```html")[1].split("```")[0]

soup = BeautifulSoup(html_content, "html.parser")

print("=== Analyzing Naukri Loaded HTML ===")
print("HTML Title:", soup.title.string if soup.title else "No Title")

# Let's search for job titles or company names
# For python developer, we expect keywords like "Python", "Developer", "Software"
# Let's find all text nodes matching "Python" or "Developer" and see their parent elements
parent_tags = set()
for text_node in soup.find_all(text=re.compile(r"Python", re.I)):
    parent = text_node.parent
    if parent and parent.name in ["a", "span", "div", "h1", "h2", "h3"]:
        parent_tags.add((parent.name, tuple(parent.get("class", []))))

print("\n--- Parent tags of text matching 'Python' ---")
for tag, classes in list(parent_tags)[:20]:
    print(f"<{tag} class='{' '.join(classes)}'>")

# Check common classes
print("\n--- Card Class checks ---")
for cls in ["srp-jobtuple-wrapper", "jobTuple", "jobTupleList", "listContainer", "cust-job-tuple", "job-tuple"]:
    elems = soup.find_all(class_=cls)
    print(f"Class '{cls}': found {len(elems)} elements")

# Print first 500 characters of page text to see what is readable
print("\n--- Text Snippet ---")
print(soup.get_text()[:1000].strip())

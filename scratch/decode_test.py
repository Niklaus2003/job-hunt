import httpx
import re
import base64

def main():
    job_page_url = 'https://remoteok.com/remote-jobs/remote-forward-deployed-engineer-agentic-platform-cohere-1131611'
    url = 'https://remoteok.com/l/1131611'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    # Use Client to automatically manage cookies!
    with httpx.Client(headers=headers, follow_redirects=True) as client:
        # Step 1: Establish session and get cookies by requesting the job details page
        print("Step 1: Requesting job details page...")
        r1 = client.get(job_page_url)
        print("Job page status:", r1.status_code)
        print("Cookies established:", list(client.cookies.keys()))
        
        # Step 2: Request the raw redirect page (passing job page as referer)
        print("\nStep 2: Requesting redirect page...")
        client.headers['Referer'] = job_page_url
        r2 = client.get(url)
        print("Redirect page status:", r2.status_code)
        
        match_n = re.search(r"n='([^']+)'", r2.text)
        if not match_n:
            print("Could not find n variable in script.")
            return
            
        n = match_n.group(1)
        
        match_key = re.search(r"split\('([^']+)'\)", r2.text)
        if not match_key:
            print("Could not find key in script.")
            return
            
        key = match_key.group(1)
        
        # Decode like JavaScript
        n = n.split(key)[1]
        inner_reversed = n[::-1]
        inner_atob = base64.b64decode(inner_reversed).decode('utf-8')
        middle_reversed = inner_atob[::-1]
        middle_split = middle_reversed.split(key)[1]
        outer_atob = base64.b64decode(middle_split).decode('utf-8')
        final_url = outer_atob.split(key)[1]
        print("Decoded relative URL:", final_url)
        
        # Step 3: Request the decoded URL
        decoded_absolute_url = "https://remoteok.com" + final_url
        print("\nStep 3: Requesting decoded URL...")
        r3 = client.get(decoded_absolute_url)
        print("Final Status code:", r3.status_code)
        print("Final Redirected URL:", r3.url)

if __name__ == "__main__":
    main()

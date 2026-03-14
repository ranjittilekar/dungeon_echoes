import urllib.request
import urllib.parse

def test_url(prompt):
    url1 = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?width=450&height=450&nologo=true"
    url2 = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=450&height=450&nologo=true"
    
    print(f"Testing URL 1 (replace space): {url1}")
    try:
        req = urllib.request.Request(url1, method='HEAD')
        resp = urllib.request.urlopen(req)
        print("URL 1 Result: ", resp.status)
    except Exception as e:
        print("URL 1 Error: ", e)

    print(f"\nTesting URL 2 (quote): {url2}")
    try:
        req = urllib.request.Request(url2, method='HEAD')
        resp = urllib.request.urlopen(req)
        print("URL 2 Result: ", resp.status)
    except Exception as e:
        print("URL 2 Error: ", e)

prompt = 'epic battle, "dragon" and knight, dark lighting'
test_url(prompt)

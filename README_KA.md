# ALEK REAL — RunPod-ის დაყენება (ქართული ინსტრუქცია)

პროექტი GitHub-ზე განახლებულია. **Python-ის 7 საცდელი ტესტი გავლილია, თუმცა RTX A6000-ზე რეალური ვიდეო ჯერ არ შექმნილა.**

## RunPod-ის ეკრანზე

1. Serverless → Deploy from GitHub → `rostomiorjonikidze-dotcom/alek-real-gpu-worker`.
2. Branch: `main`; Dockerfile: `/Dockerfile`; რეჟიმი: **Queue**.
3. GPU Configuration → **Previous generation** → **RTX A6000 (48 GB)** ან **A40 (48 GB)**.
4. **Max workers = 1; Active workers = 0; GPU count = 1**.
5. Initialization timeout → **900 sec**. Execution timeout → **1800 sec**. Idle timeout → **5 sec**.
6. **Cached model**: `Wan-AI/Wan2.2-TI2V-5B-Diffusers`.
7. Environment variables: `ALEK_ENABLE_GPU_INFERENCE=false` (ამ ეტაპზე). შენახვის დომენი ავტომატურად შეირჩევა; სურვილისამებრ `ALEK_STORAGE_HOST=aqjpznneffqhpbiydejv.supabase.co`.
8. Docker build-ისთვის შეგიძლია Deploy Endpoint-ის გამოყენება მხოლოდ RunPod-ის ფასისა და ანგარიშის პირობების გადამოწმების შემდეგ. **Active workers=0 არ ნიშნავს, რომ ყველა ხარჯი ნულია; ტესტი Worker-ს აამუშავებს და თანხას ჩამოჭრის.**

## შემდეგი სავალდებულო ნაბიჯები პირველი MP4-მდე

- RunPod Endpoint-ის Builds სექციაში Docker build წარმატებით დასრულდეს.
- RunPod-ში ენდპოინტის ID და API გასაღები Supabase-ის **Edge Function Secrets**-ში პირადად ჩაიწეროს.
- ALEK REAL-ის Supabase მომხმარებელს მფლობელის role მიენიჭოს ანგარიშის მფლობელობის დამადასტურებელი შემოწმების შემდეგ.
- Supabase-ის დღიური და თვიური ბიუჯეტი ზომიერად გავააქტიუროთ.
- RunPod-ის environment-ში `ALEK_ENABLE_GPU_INFERENCE=true` ვქნათ მხოლოდ პირველი კონტროლირებადი GPU ტესტის წინ.
- სატესტოდ გამოიყენეთ **5 წამი, 16:9**; გადაამოწმეთ რეალური MP4-ის მიღება და ჩამოტვირთვა.
- `video.alek.best`-ის ძველი გვერდი ჯერ ახალ Gateway-ს არ იყენებს: საჭიროა Frontend-ის ახალი დაკავშირება.

**ყურადღება:** ეს არის მფლობელის სატესტო რეჟიმი, არა უკვე მზადებული საჯარო ფასიანი ვიდეოგენერატორი. Image-to-Video, გადახდები, GPU-ზე რეალური ტესტი და საჯარო ინტერფეისი კიდევ გასამართია.

დამხმარე დოკუმენტაცია:
- https://docs.runpod.io/serverless/workers/github-integration
- https://docs.runpod.io/serverless/endpoints/model-caching
- https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B-Diffusers

import asyncio
from database import SessionLocal
from sqlalchemy import text

async def main():
    print('\n==================================================================')
    print('=== ?? KET QUA BOC TACH AM THANH & HINH ANH TU VIDEO THAT ===')
    print('==================================================================\n')
    
    async with SessionLocal() as db:
        try:
            q_asset = text('SELECT file_name, duration_sec, full_transcript FROM assets ORDER BY ingested_at DESC LIMIT 1')
            res_asset = await db.execute(q_asset)
            asset = res_asset.fetchone()
            if asset:
                print(f'?? File Video: {asset[0]} ({asset[1]} giay)')
                print(f'??? Toan bo loi thoai (Full Transcript):\n\"{asset[2]}\"\n')
        except Exception as e:
            print('Loi doc asset:', str(e))

        print('------------------------------------------------------------------')
        print('?? CHI TIET TUNG PHAN CANH (SCENES):')
        print('------------------------------------------------------------------')
        try:
            q_scenes = text('SELECT scene_index, timestamp_start_sec, timestamp_end_sec, transcript_snippet, caption FROM scenes ORDER BY scene_index ASC LIMIT 5')
            res_scenes = await db.execute(q_scenes)
            scenes = res_scenes.fetchall()
            for s in scenes:
                print(f'?? Phan thu {s[0]} [{s[1]}s -> {s[2]}s]:')
                print(f'   - Loi thoai nghe duoc: \"{s[3]}\"')
                print(f'   - AI nhin anh mo ta  : \"{s[4]}\"')
                print('-' * 40)
        except Exception as e:
            print('Loi doc scenes:', str(e))

asyncio.run(main())

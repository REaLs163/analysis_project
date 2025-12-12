import os
import fitz  # PyMuPDF 1.26.6
import boto3
from dotenv import load_dotenv

load_dotenv()

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
S3_ENDPOINT = os.getenv("S3_ENDPOINT") 
S3_BUCKET = os.getenv("S3_BUCKET")

INPUT_PREFIX = "input/"
OUTPUT_PREFIX = "output/"

# Инициализация клиента S3
s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

def find_red_text(page):
    red_text_items = []
    text_instances = page.get_text("dict")["blocks"]

    for block in text_instances:
        if "lines" in block:
            for line in block["lines"]:
                for span in line["spans"]:
                    color = span["color"]
                    r = (color >> 16) & 0xFF
                    g = (color >> 8) & 0xFF
                    b = color & 0xFF

                    if r > 150 and g < 100 and b < 100:
                        red_text_items.append({
                            "bbox": span["bbox"],
                            "text": span["text"]
                        })

    return red_text_items

def find_exclamation_marks(page):
    exclamation_items = []
    text_instances = page.get_text("dict")["blocks"]

    for block in text_instances:
        if "lines" in block:
            for line in block["lines"]:
                for span in line["spans"]:
                    if "!" in span["text"]:
                        color = span["color"]
                        r = (color >> 16) & 0xFF
                        g = (color >> 8) & 0xFF
                        b = color & 0xFF

                        if r > 150 and g < 100 and b < 100:
                            exclamation_items.append({
                                "bbox": span["bbox"],
                                "text": span["text"]
                            })

    return exclamation_items

def expand_bbox_to_line(bbox, page):
    x0, y0, x1, y1 = bbox
    line_height = y1 - y0
    page_width = page.rect.width

    expanded_bbox = (
        0,
        y0 - line_height * 0.001,
        page_width,
        y1 + line_height * 0.001
    )

    return expanded_bbox

def process_pdf_bytes(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    has_deviations = False

    for page_num in range(len(doc)):
        page = doc[page_num]

        red_text = find_red_text(page)
        exclamations = find_exclamation_marks(page)
        all_deviations = red_text + exclamations

        if all_deviations:
            has_deviations = True
            lines_dict = {}

            for item in all_deviations:
                y_pos = round(item["bbox"][1], 1)
                if y_pos not in lines_dict:
                    lines_dict[y_pos] = []
                lines_dict[y_pos].append(item)

            for y_pos, items in lines_dict.items():
                x0 = min(item["bbox"][0] for item in items)
                y0 = min(item["bbox"][1] for item in items)
                x1 = max(item["bbox"][2] for item in items)
                y1 = max(item["bbox"][3] for item in items)

                line_bbox = expand_bbox_to_line((x0, y0, x1, y1), page)

                highlight = page.add_rect_annot(line_bbox)
                highlight.set_colors(stroke=(1, 0, 0), fill=(1, 0, 0))
                highlight.set_opacity(0.3)
                highlight.update()

    output_pdf_bytes = doc.tobytes() if has_deviations else b""
    doc.close()
    return has_deviations, output_pdf_bytes


def handler(event, context):

    print("Cloud Function triggered")
    print(f"Event: {event}")

    if "messages" not in event:
        print("Нет сообщений в event → завершение.")
        return {"status": "no_messages"}

    for msg in event["messages"]:

        obj = msg["details"]["object_id"]

        if isinstance(obj, str):
            key = obj
        else:
            key = obj["key"]
        print(f"Получен файл: {key}")

        # Проверяем тип файла
        if not key.lower().endswith(".pdf"):
            print("Файл не PDF → пропущен.")
            continue

        # Проверяем префикс
        if not key.startswith(INPUT_PREFIX):
            print("Файл не из input/ → пропущен.")
            continue

        # Скачать PDF
        pdf_bytes = s3.get_object(Bucket=S3_BUCKET, Key=key)["Body"].read()

        # Обработать PDF
        has_dev, output_bytes = process_pdf_bytes(pdf_bytes)

        if not has_dev:
            print("Отклонений нет → в output/ не сохраняем.")
            continue

        # Сохранить в output/
        filename = key.split("/")[-1]
        output_key = f"{OUTPUT_PREFIX}{filename}"

        s3.put_object(
            Bucket=S3_BUCKET,
            Key=output_key,
            Body=output_bytes,
            ContentType="application/pdf"
        )

        print(f"Сохранён → s3://{S3_BUCKET}/{output_key}")

    return {"status": "done"}
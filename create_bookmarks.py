#!/usr/bin/env python3
import os.path
import sys
import re

import pymupdf

# 感谢 Gemini

def get_dest(bbox):
    # 提取文本左上角的精确坐标 (x0, y0)
    x0 = bbox[0]
    y0 = bbox[1]

    # 3. 构建精确的目标字典 (Destination)
    dest = {
        "kind": pymupdf.LINK_GOTO,  # 指定这是一个跳转链接
        "to": pymupdf.Point(x0, y0),  # 精确跳转到这段文字的 X/Y 坐标
        "zoom": 0.0  # 0.0 表示跳转后保持用户当前的缩放比例不变
    }

    # 4. 将书签加入 TOC 列表
    # 格式: [层级(int), 标题(str), 页码(1起步), 目标字典(dict)]
    return dest


def create_bookmarks(input_pdf, output_pdf):
    doc = pymupdf.open(input_pdf)
    toc = []

    is_created_xyb = False
    is_created_zzb = False

    cur_nikaya = None

    for page_num in range(len(doc)):
        page = doc[page_num]

        # 1. 以字典形式获取页面上的所有文本及其排版信息
        text_dict = page.get_text("dict")

        # 字典的结构是嵌套的：blocks(块) -> lines(行) -> spans(片段)
        for block in text_dict.get("blocks", []):
            if block["type"] == 0:  # type 为 0 代表这是纯文本块（非图片）
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span["text"].strip()
                        size = span["size"]  # 字体大小 (比如 12.0, 15.5)
                        bbox = span["bbox"]  # 坐标 (x0, y0, x1, y1)

                        if not size > 14:
                            continue
                        if text == "◆":
                            continue
                        if text == "。":
                            continue

                        m1 = re.match(r"^長部$", text)
                        m2 = re.match(r"^中部$", text)
                        m3 = re.match(r"^相應部．([一二三四五六七八九十]+．\S+相應)$", text)
                        m4 = re.match(r"^增支部．(第[一二三四五六七八九十]+集)$", text)
                        m = m1 or m2 or m3 or m4
                        if m:
                            dest = get_dest(bbox)

                            if m is m1:
                                cur_nikaya = "d"
                                toc.append([1, text, page_num + 1, dest])
                            elif m is m2:
                                cur_nikaya = "m"
                                toc.append([1, text, page_num + 1, dest])
                            if m is m3:
                                cur_nikaya = "s"
                                if not is_created_xyb:
                                    toc.append([1, "相應部", page_num + 1, dest])
                                    is_created_xyb = True
                                toc.append([2, m.group(1), page_num + 1, dest])

                            elif m is m4:
                                cur_nikaya = "a"
                                if not is_created_zzb:
                                    toc.append([1, "增支部", page_num + 1, dest])
                                    is_created_zzb = True
                                toc.append([2, m.group(1), page_num + 1, dest])
                            continue

                        m1 = re.match(r"^[一二三四五六七八九十零]+．\S+$", text)
                        m2 = re.match(r"^[一二三四五六七八九十零]+至[一二三四五六七八九十零]+經$", text)
                        m3 = re.match(r"\S+", text)
                        m = m1 or m2 or m3
                        if m:
                            if cur_nikaya in "dm":
                                level = 2
                            else:
                                level = 3
                            dest = get_dest(bbox)
                            toc.append([level, text, page_num + 1, dest])
                            # .replace("．", "·")
                        else:
                            if len(text) > 1:
                                print("what?", repr(text))

    # 5. 将带坐标的书签写入 PDF
    doc.set_toc(toc)

    doc.save(output_pdf) #garbage=4, clean=True
    doc.close()


def main():
    args = sys.argv[1:]
    output_pdf = "蕭式球_漢譯經藏_四部合訂本_含書籤.pdf"
    if len(args) == 0:
        input_pdf = "四部合成 2.pdf"
    elif len(args) == 1:
        input_pdf = args[0]
    else:
        print(len(args))
        input_pdf = args[0]
        output_pdf = args[1]

    create_bookmarks(input_pdf, output_pdf)
    print("书签生成完毕：", os.path.abspath(output_pdf))


if __name__ == "__main__":
    main()

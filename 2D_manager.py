from PIL import Image

# 打開有空白的原圖
img = Image.open("./textures/gui/container/inventory.png")

# 設定裁切範圍 (左, 上, 右, 下)
# 灰色背包主體剛好在左上角，所以從 (0, 0) 開始，切到 (176, 166)
clean_box = (0, 0, 176, 166)
inventory_clean = img.crop(clean_box)

# 儲存成乾淨、沒有空白的背包圖
inventory_clean.save("./images/ui/inventory_clean.png")

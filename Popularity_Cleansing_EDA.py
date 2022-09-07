import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from plotly.offline import plot
from wordcloud import WordCloud, STOPWORDS

# set path
path1 = "/Users/remikc/Programming/Python/OnePage/Data/"
path2 = "/Users/remikc/Programming/Python/OnePage/Plot/"

# load data
netflix = pd.read_csv(path1+"netflix_new.csv")
TW = pd.read_csv(path1+"TW.csv")

# 中文設定
plt.rcParams["font.family"] = ["Heiti TC"]
plt.rcParams["font.size"] = 13


#%% Modify genres to reduce categories

# 自訂處理dataframe的函式
def regex_genre(df):
    # 只保留Netflix官網公告的大分類項目
    new_genre = {
        "listed_in":{
            r'International|Independent|Crime|Reality|British|Spanish-Language|Korean|LGBTQ|Mysteries|Science & Nature|Teen|Faith & Spirituality':"",
            r'Kids':"Children & Family",
            r'Stand-Up Comedy & Talk Shows':"Comedies",
            r'Docuseries':"Documentaries",
            r'Music & Musicals':"Music",
            r'Classic & Cult':"Classic"}
        }
    df = df.replace(new_genre, regex=True)
    # 清除除非字元開頭和結尾，以及多餘的逗號
    df = df.replace({"listed_in":{r'^\W+|\W+$':"",r'(, )+':", "}}, regex=True)
    # 沒有值的地方補NAN
    df["listed_in"] = df["listed_in"].replace("", np.nan)
    return df

# pipe 將自訂函式套用在dataframe
TW = TW.pipe(regex_genre)
netflix = netflix.pipe(regex_genre)


#%% 哪些因素影響作品是否熱門1（影片類型Ｘ影視分類）
# 前提：因為上次資料分析Project中觀察到「台灣作品品質還不錯(評分>7.3有20%以上)但是不賣座（熱門作品<5%）」

# 建立熱門影片類型df
pop = netflix[(netflix["numVotes"]>3000)&(netflix["averageRating"]>7.3)]
pop_genre = pop[["type", "listed_in"]]
# 建立所有影片類型df
genre = netflix[["type", "listed_in"]] 

# 函式化df處理流程
def explode_genre(df, colname):
    df.dropna(inplace=True)
    df = df.reset_index(drop=True)
    df["listed_in"] = df["listed_in"].str.split(", ").reset_index(drop=True)
    df = df.explode("listed_in")
    df = df.groupby(["type", "listed_in"]).size().reset_index().rename(columns={0:colname})
    return df

# pipe 將自訂函式套用在dataframe
pop_genre = pop_genre.pipe(explode_genre, "count")
genre = genre.pipe(explode_genre, "total")

# 合併df並計算比例
pop_percent = pop_genre.merge(genre, how="left", on=["type", "listed_in"])
pop_percent["percent"] = pop_percent["count"]/pop_percent["total"]*100
pop_percent["all"] = 100
pop_percent.sort_values(by=["type", "percent"], ascending=[True, False], inplace=True)

#%% 世界影片熱門度(影片類型Ｘ影視分類) 作圖
movie = pop_percent[pop_percent["type"]=="Movie"].reset_index(drop=True)
TV = pop_percent[pop_percent["type"]=="TV Show"].reset_index(drop=True)

plt.figure(figsize = (14, 16), dpi=200)

ax1 = plt.subplot(211)
sns.barplot(x="all", y="listed_in", data=movie,
            label="非熱門", color="#221F1F")

sns.barplot(x="percent", y="listed_in", data=movie,
            label="熱門", color="#B81D24")

for i in range(len(movie)):
    ax1.annotate(f"{movie['percent'][i]:.3}%", 
                    xy=(movie['percent'][i]/2, i),
                    fontsize=12, color="#F5F5F1",
                    va="center", ha="center")

plt.title("Netflix_Movie 各類型影片中 熱門影片比例", fontsize=21, loc="left")
plt.title("熱門：評分>7.3| 評分人數>3000             ", fontsize=12, loc="right")
ax1.legend(ncol=2, loc="lower right", shadow=True)
ax1.set(ylabel="", xlabel="")
plt.xticks(np.arange(0, 101, 10))
    
ax2 = plt.subplot(212)
sns.barplot(x="all", y="listed_in", data=TV,
            label="非熱門", color="#221F1F")

sns.barplot(x="percent", y="listed_in", data=TV,
            label="熱門", color="#B81D24")

for i in range(len(TV)):
    ax2.annotate(f"{TV['percent'][i]:.3}%", 
                    xy=(TV['percent'][i]/2, i),
                    fontsize=12, color="#F5F5F1",
                    va="center", ha="center")

plt.title("Netflix_TV Show 各類型影片中 熱門影片比例", fontsize=21, loc="left")
plt.title("熱門：評分>7.3| 評分人數>3000             ", fontsize=12, loc="right")
ax2.legend(ncol=2, loc="lower right", shadow=True)
ax2.set(ylabel="", xlabel="")
plt.xticks(np.arange(0, 101, 10))

sns.despine()
plt.subplots_adjust(wspace=0.18)

# 存檔
plt.savefig(path2+"popular_genre.png", bbox_inches="tight")
plt.show()

#%% 臺灣 影片類型分佈（/電影電視/劇情喜劇愛情恐怖)
# 建立dataframe
TWgenre = netflix[netflix["country_main"]=="Taiwan"][["type", "listed_in"]]
# pipe 將自訂函式套用在dataframe
TWgenre = TWgenre.pipe(explode_genre, "count")

# 作圖
fig = px.sunburst(TWgenre, 
                  path=["type", "listed_in"], values="count",
                  color="count", color_continuous_scale="matter", 
                  title="Netflix 臺灣影片類型分佈比例")
fig.update_traces(textinfo="label+percent parent")
fig.update_layout(coloraxis_colorbar_title="數量") 
plot(fig)

#%% 輸出台灣熱門作品表
TWpop = TW[(TW["numVotes"]>3000)&(TW["averageRating"]>7.3)][["type", "title", "director", "listed_in", "numVotes", "averageRating"]]

fig = plt.figure(figsize = (12, 3), dpi=200)
ax = fig.add_subplot(111, frame_on=False)
ax.xaxis.set_visible(False) 
ax.yaxis.set_visible(False)

the_table = plt.table(cellText=TWpop.values,
                      colWidths=[0.065, 0.27, 0.16, 0.26, 0.075, 0.035],
                      rowLabels=["" for i in range(2)],
                      colLabels=["影視類型", "片名", "導演", "影片類型", "評分人數", "評分"],
                      loc="center left",
                      cellLoc="center",
                      cellColours=[["gold" if i in [0,3] else "white" for i in range(6)] for i in range(2)],
                      colColours=["indianred" for i in range(6)])

the_table.auto_set_font_size(False) 
the_table.set_fontsize(20)
the_table.scale(2, 4)
plt.title("   Netflix 臺灣熱門作品表 （評分>7.3| 評分人數>3000）", fontsize=24, loc="left")

plt.savefig(path2+"TWpop_table.png", bbox_inches="tight")
plt.show()

#%% 哪些因素影響作品是否熱門2（影片內容:影片描述）

Pop = netflix[(netflix["numVotes"]>3000)&(netflix["averageRating"]>7.3)]
# 將description內容合併儲存成整段文字
Pop_text = Pop["description"].str.cat(sep=" ")
TWdesc_text = TW["description"].str.cat(sep=" ")

# 設定新增stopwords
stopwords = set(STOPWORDS)
stopwords.update({"one", "two", "three", "s", "year", "years"})

# 文字雲繪圖
plt.figure(figsize = (18, 10), dpi=300)

plt.subplot(211)
Pop_cloud = WordCloud(max_words=2000, max_font_size=70, background_color="white",
        stopwords=stopwords,random_state=105).generate(Pop_text) 

plt.imshow(Pop_cloud) 
plt.title("Netflix 熱門影片內容（影片簡述）", loc="left")
plt.axis("off")


plt.subplot(212)
TW_cloud = WordCloud(max_words=2000, max_font_size=70, background_color="white",
        stopwords=stopwords,random_state=105).generate(TWdesc_text) # background_color="white"

plt.imshow(TW_cloud) 
plt.title("Netflix 臺灣影片內容（影片簡述）", loc="left")
plt.axis("off")

plt.subplots_adjust(wspace=0.01)
plt.savefig(path2+"WCloud_ver.png", bbox_inches="tight")
plt.show()

#%% 上架作品分析：劇荒期vs.劇豐期在哪個月份？
import calendar
# 因為台灣最先上架的作品是在2016-08，這裡只採用2016-08(含)之後的數據(Netflix 8503筆, TW 85筆)
add_m = netflix[netflix["f_date_add_Ym"]>="2016-08"][["f_date_add_Ym", "f_date_add_m"]]

def month_mean(df, string):
    # 按月份計算平台每月平均上架影片數量
    df = df.groupby(["f_date_add_Ym", "f_date_add_m"]).size().groupby(["f_date_add_m"]).mean().reset_index()
    # 月份轉換成縮寫
    df["f_date_add_m"] = df["f_date_add_m"].apply(lambda x: calendar.month_abbr[int(x)])
    df = df.rename(columns={0:"mean"})
    df["loc"] = string
    return df

add_m_mean = add_m.pipe(month_mean, "world")
add_m_mean_TW = TW.pipe(month_mean, "TW")
add_m_mean = pd.concat([add_m_mean, add_m_mean_TW]).reset_index(drop=True)

# 看一下Netflix全部資料分佈跟標準差
add_m_mean[add_m_mean["loc"]=="world"].describe()
'''
            mean
count   12.000000
mean   137.522222
std     14.700665
min    108.000000
25%    126.166667
50%    139.500000
75%    145.950000
max    158.200000
'''
# 看一下TW分佈跟標準差
add_m_mean[add_m_mean["loc"]=="TW"].describe()
'''
            mean
count  12.000000
mean    2.256944
std     1.026455
min     1.000000
25%     1.187500
50%     2.250000
75%     3.062500
max     3.666667
'''

#%% 劇荒期vs.劇豐期 對照 台灣各月上架數量
# 作圖
import matplotlib.gridspec as gridspec
# 設定上下方兩個子圖比例
gs = gridspec.GridSpec(2, 1, height_ratios=[13, 1])
fig = plt.figure(figsize = (10, 4), dpi=200)
fig.subplots_adjust(hspace=0.13)
ax1 = fig.add_subplot(gs[0])
ax2 = fig.add_subplot(gs[1])

# 畫折線圖
sns.lineplot(ax=ax1, x="f_date_add_m", y="mean", hue="loc", data=add_m_mean,palette=["#B81D24", "#113CCF"],
             hue_order=["world", "TW"], marker="o", markeredgecolor=None, alpha=.8)
sns.lineplot(ax=ax2, x="f_date_add_m", y="mean", hue="loc", data=add_m_mean,palette=["#B81D24", "#113CCF"],
             hue_order=["world", "TW"], marker="o", markeredgecolor=None, alpha=.8)
# 平均值線
mean_all = add_m_mean[add_m_mean["loc"]=="world"]["mean"].mean()
ax1.axhline(mean_all,ls="--", lw=1.2, c="#221F1F", alpha=.5)

# +-1個標準差線
std_all = add_m_mean[add_m_mean["loc"]=="world"]["mean"].std()
ax1.axhline(mean_all+std_all,ls="-.", lw=1.2, c="#B81D24", alpha=.5)
ax1.axhline(mean_all-std_all,ls="-.", lw=1.2, c="#B81D24", alpha=.5)

y_all = list(add_m_mean[(add_m_mean["loc"]=="world")&((add_m_mean["f_date_add_m"]=="Jul")|(add_m_mean["f_date_add_m"]=="Dec"))]["mean"])
x_all = ["Jul", "Dec"]
ax1.scatter(x=x_all, y=y_all, marker="^", s=200, c="#B81D24")

y_all2 = list(add_m_mean[(add_m_mean["loc"]=="world")&((add_m_mean["f_date_add_m"]=="Feb")|(add_m_mean["f_date_add_m"]=="May"))]["mean"])
x_all2 = ["Feb", "May"]
ax1.scatter(x=x_all2, y=y_all2, marker="v", s=200, c="#B81D24")

for x, y in zip(x_all, y_all):
    ax1.text(x, y, x,fontsize=16, c="Maroon")
for x, y in zip(x_all2, y_all2):
    ax1.text(x, y, x,fontsize=16, c="#221F1F")

# broken axis設定
ax1.set_ylim(100, 160)  # 界外值所在區域
ax2.set_ylim(0, 5)  # 其他資料點
ax1.spines[["bottom", "top", "right"]].set_visible(False) # 移除子圖(上)的下、上、右邊框
ax2.spines[["top", "right"]].set_visible(False) # 移除子圖(下)的上、右邊框
ax1.xaxis.tick_top() # 將子圖(上)的x-tick移到上方
ax1.tick_params(which="both", top=False, labeltop=False)  # 不顯示子圖(上)的x-tick和標籤

# 繪製刪除線
d = .5  
kwargs = dict(marker=[(-1, -d), (1, d)], markersize=12,
              linestyle="none", color='r', mec='r', mew=1, clip_on=False)
ax1.plot([0],[0], transform=ax1.transAxes, **kwargs)
ax2.plot([0],[1], transform=ax2.transAxes, **kwargs)

# 圖表標籤設定
fig.suptitle("   Netflix 各月份平均上架影片數量 |點虛線為平均值上下一個標準差區間", fontsize=18, y=0.98)  
ax2.set_xlabel("月份", fontsize=18, labelpad=8)
ax1.set_ylabel("影\n片\n數\n量", rotation=0, fontsize=18, labelpad=15)
ax1.set_xlabel("")
ax2.set_ylabel("")
ax1.legend(labels=["所有國家| 2016/08 - 2021/09", "臺灣        | 2016/08 - 2021/09"]) 
ax2.legend().set_visible(False)          
ax1.grid()
ax2.grid()

# 存檔
plt.savefig(path2+"add_M.png", bbox_inches="tight")
plt.show()

#%% 效益評估1

# 假如動作、懸疑、科幻片的數量增加10％
print("假如電視作品中，動作、懸疑、科幻片的數量增加10％，熱門影片的比例至少增長%.2f倍(%.2f%%)" % (((4.71+10*36.9/100)/4.71), 10*36.9/100))
# 假如電視作品中，動作、懸疑、科幻片的數量增加10％，熱門影片的比例至少增長1.78倍(3.69%)


#%% 效益評估2
print("臺灣平均每年上架%d部影片" % add_m_mean_TW["mean"].sum())
# 臺灣平均每年上架27部影片

feb_all = add_m_mean[(add_m_mean["loc"]=="world")&(add_m_mean["f_date_add_m"]=="Feb")]["mean"]
feb_tw_ori = add_m_mean_TW[add_m_mean["f_date_add_m"]=="Feb"]["mean"]
feb_tw_new = round(add_m_mean_TW["mean"].sum(), 0)

print("原本二月上架影片的能見度為：%.2f%%" % (feb_tw_ori/feb_all*100))
print("集中二月上架的話，影片能見度為：%.2f%%" % (feb_tw_new/feb_all*100))
print("能見度提高：%.2f%%" % (feb_tw_new/feb_all*100-feb_tw_ori/feb_all*100))

# 原本二月上架影片的能見度為：1.85%
# 集中二月上架的話，影片能見度為：25.00%
# 能見度提高:23.15%




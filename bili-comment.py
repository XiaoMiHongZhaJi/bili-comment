import requests
import re
import jieba
import wordcloud
import time
import sys
import pandas as pd


class Bilibili:
	def __init__(self, video_url, page, file_name):

		self.barrage = None
		self.aid = None
		self.cid = None
		self.page = page
		self.file_name = file_name
		self.baseurl = video_url.split('?')[0]

	# 爬取弹幕和评论
	def get_aid_cid(self):
		cid_url = self.baseurl + "?p=" + self.page
		cid_regx = '{"cid":([\d]+),"page":%s,' % self.page
		aid_regx = '"aid":([\d]+),'
		r = requests.get(cid_url)
		r.encoding = 'utf-8'
		try:

			self.cid = re.findall(cid_regx, r.text)[0]
			self.aid = re.findall(aid_regx, r.text)[int(self.page) - 1]
		except:
			print('视频序号输入有误，请保证序号在1到最大值之间！')
			time.sleep(3)
			sys.exit()

	def get_barrage(self):
		print('正在获取弹幕......')

		comment_url = 'https://comment.bilibili.com/' + self.cid + '.xml'

		# 获取并提取弹幕 #
		r = requests.get(comment_url)
		r.encoding = 'utf-8'
		content = r.text
		# 正则表达式匹配字幕文本
		comment_list = re.findall('>(.*?)</d><d ', content)

		# jieba分词
		self.barrage = " ".join(comment_list)

	def get_comment(self, x, y):
		excel_data = []
		excel_columns = ["序号", "发送时间", "用户名", "性别", "等级", "评论", "子评论"]
		index = 0
		for i in range(x, y + 1):
			r = requests.get('https://api.bilibili.com/x/v2/reply?pn={}&type=1&oid={}&sort=2'.format(i, self.aid)).json()
			replies = r['data']['replies']
			if replies is None or len(replies) == 0:
				print('------没有评论了，共获取了{}条评论------'.format(index))
				break
			print('------评论列表------')
			for reply in replies:
				index += 1
				try:
					message = reply['content']['message']
					ctime = reply['ctime']
					date_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ctime))
					member = reply['member']
					uname = member['uname']
					sex = member['sex']
					level = member['level_info']['current_level']
					replies_text = ''
					replies_list = reply['replies']
					if replies_list is not None:
						try:
							for reply_ in replies_list:
								member_ = reply_['member']
								uname_ = member_['uname']
								sex_ = member_['sex']
								message_ = reply_['content']['message']
								replies_text += "{}({})：{}\n".format(uname_, sex_, message_)
						except Exception as e1:
							print(e1)
					excel_data.append([index, date_time, uname, sex, level, message, replies_text])
					print(index, message)
					self.barrage += " " + message
				except Exception as e:
					print(e)
		export_excel(excel_data, excel_columns, self.file_name)
		pass

	def gen_word_cloud(self):
		print('正在分词......')

		text = "".join(jieba.lcut(self.barrage))
		# 实例化词云，
		wc = wordcloud.WordCloud(
			# 选择字体路径，没有选择的话，中文无法正常显示
			font_path='C:/Windows/Fonts/simsun.ttc',
			width=2560,
			height=1440,
			# min_font_size=4,
			# max_font_size=10,
		)
		# 文本中生成词云
		wc.generate(text)
		# 保存成图片
		wc.to_file(file_name + ".jpg")
		print('词云生成完毕，图片名称：{}.jpg'.format(self.file_name))


def export_excel(data, columns, file_name):
	try:
		df = pd.DataFrame(data, columns=columns)
		writer = pd.ExcelWriter(file_name + ".xlsx")
		df.to_excel(writer, index=False)
		writer._save()
	except Exception as e:
		print(e)


def check_url(url):
	try:
		r = requests.get(url)
	except:
		return None
	r.encoding = 'utf-8'
	# 视频名称正则表达式
	regx = '"part":"(.*?)"'
	r.encoding = 'utf-8'
	result = re.findall(regx, r.text)
	count = 0
	if len(result) > 0:
		print('------视频列表------')
		for i in result:
			count += 1
			print("视频" + str(count) + " : " + i)
		return result[0]
	return None


if __name__ == '__main__':
	# 视频地址
	video_url = input("请输入视频地址，例如：https://www.bilibili.com/video/BV1XX4y1H7C5\n")

	if video_url is None or video_url == '':
		video_url = "https://www.bilibili.com/video/BV1XX4y1H7C5"

	title = check_url(video_url)

	if title is None:
		print('视频地址无效\n')
		exit(-1)

	print('------视频地址有效------\n')

	# 第n个视频
	page = input('请输入视频的序号，默认1：')

	if page is None or page == '':
		page = '1'

	# 图片储存路径
	file_name = input('请输入生产词云图片名称，默认视频标题+时间：')

	if file_name is None or file_name == '':
		file_name = "{}_{}".format(title, time.strftime("%Y-%m-%d_%H_%M_%S", time.localtime(time.time())))

	# 计时
	start_time = time.time()

	# 实例化类
	b = Bilibili(video_url, page, file_name)

	# 获取aid和cid
	b.get_aid_cid()

	# 获取弹幕
	b.get_barrage()

	# 获取评论 起始页和结束页
	# 如需获取所有评论，将结束页改大即可
	b.get_comment(1, 2)

	# 生成词云
	b.gen_word_cloud()

	print('程序运行完毕，耗时:{:.2f}s'.format(time.time() - start_time))

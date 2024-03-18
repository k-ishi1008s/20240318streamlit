import streamlit as st
import sqlite3
import time
from datetime import datetime
import pandas as pd
from PIL import Image
import io

st.header("AIによって生成したピクトグラムの評価実験")


#----変数定義ゾーン

if 'user_name' not in st.session_state:
    st.session_state.user_name = None
if 'access_check' not in st.session_state:
    st.session_state.access_check = False
data = None
imgsum = 50 #画像の合計枚数
sleeptime = 5 #表示時間
countdown = 25 #表示時間＋カウントダウン＝制限時間
timelimit = sleeptime + countdown
image_folder = './images/' #出題する画像の格納場所
blackImg = Image.open('black.png')
#ユーザーチェック
if 'user_check' not in st.session_state:
    st.session_state.user_check = True
#例題
if 'example' not in st.session_state:
    st.session_state.example = False
#画像番号
if 'imgIndex' not in st.session_state:
    st.session_state.imgIndex = 1
#回答時間と制限時間
if 'timestamps' not in st.session_state:
    st.session_state.timestamps = {f'{i+1}': {'start': None, 'save': None, 'sleeptime':sleeptime, 'countdown': countdown} for i in range(imgsum)}
#連続して問題を出す用
if 'otherQ' not in st.session_state:
    st.session_state.otherQ = False
#ページ番号
if 'page_id' not in st.session_state:
    st.session_state.page_id = 'page1'

#---変数定義ゾーン
    

if st.session_state.page_id == 'page1':
    #以下冒頭
    st.markdown("""
                評価実験にご協力いただき，ありがとうございます．
                
                本実験は画像生成モデルpix2pixによって生成されたピクトグラムが何に見えるかアンケートをとり，その結果を分析することで画像生成モデルの評価を行うことを目的としています．

                実験にかかる時間は約15分です．

                本実験への参加は任意であり，一度同意した場合でも，いつでも同意を撤回し実験を中断することが可能です．その場合，希望に応じて提供いただいたデータは破棄いたします．
                
                参加者から得たデータや個人情報は実験後，分析を行うために必要な範囲において利用いたします．

                質問等あれば下記までご連絡ください．

                和歌山大学システム工学部　石橋孝太郎 
                
                E-mail: s256016@wakayama-u.ac.jp 

                ---
    """)
    st.subheader('概要説明')
    #実験概要
    st.markdown("""
                実験は **約15分**で終わります．

                今から，50個のピクトグラムを見てもらい，そのピクトグラムが何に見えるか，テキストボックスへ入力してもらいます．

                手順は以下の通りです．休憩はどこでとってもらってもいいです．

                &ensp;

                1. テキスト入力ボックスへユーザー名をアルファベットで入力してください．ユーザー名はハンドルネームで構いません．
                他の人との被りを防ぐため，ハンドルネーム＋好きな数字４桁にしていただきたいです．
                
                2. 簡単な個人情報の入力，例題を行なった後，**アンケートを開始**をクリックしてください．アンケート画面へ移ります．
                
                3. アンケート画面に映ると，**（１）を表示**ボタンが出てきます．このボタンをクリックするとアンケート開始です．
                
                4. ボタンをクリックすると，ピクトグラムが**５秒間**表示されます．
                何を表したピクトグラムなのか考え，下の **テキストボックスへ入力** してください．
                
                5. 回答の制限時間は **合計30秒** です．初めの5秒間はピクトグラムが表示されます．残りの25秒間はピクトグラムを見ることができなくなります．
                
                6. 入力が完了したら，**回答を送信**をクリックしてください．制限時間以内に入力できていると **保存完了** と表示されます．
                
                7. **閉じる** をクリックして次の問題へ進んでください．
                
                8. 4~7を50個のピクトグラムで行ってもらいます．
                
                以下がデモ動画です．    
    """)
    st.video('./demo.mov')
    st.divider()
    if st.session_state.user_check:
        if st.checkbox("以上の内容に同意していただけたら、チェックを入れてください"):
            st.divider()
            # ユーザー名入力フォーム
            st.session_state.user_name = st.text_input('ユーザー名をアルファベット+数字４文字で入力してください', 'name0000')
            st.text('ユーザー名は一度しか入力できません')
    else:
        st.success(f'あなたのユーザー名は {st.session_state.user_name} です')

conn = sqlite3.connect('data2.db')
c = conn.cursor()

if st.session_state.user_name is not None and st.session_state.access_check==False:
    # 入力を保存するテーブル
    c.execute(f'''
        CREATE TABLE IF NOT EXISTS {st.session_state.user_name}(
            image_number INTEGER,
            input_text TEXT,
            time REAL,
            timelimit BOOLEAN
        )
    ''')
    conn.commit()
    data = c.execute(f'SELECT * FROM {st.session_state.user_name}').fetchall()
    if data:
        st.warning('このユーザー名は使用できません！')
    else:
        st.success('このユーザー名は使用可能です！')
        st.session_state.access_check = True
    #Excelファイル生成
    all_data = c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';").fetchall()
    excel_data = io.BytesIO()
    with pd.ExcelWriter(excel_data, engine='openpyxl') as writer:
        pd.DataFrame(columns=[]).to_excel(writer, index=False, sheet_name='EmptySheet', header=True)
        for table_name, in all_data:
            user_df = pd.read_sql_query(f'SELECT * FROM {table_name}', conn)
            user_df.to_excel(writer, index=False, sheet_name=table_name, header=True)
    #ファイルの先頭に戻す
    excel_data.seek(0)
    if st.session_state.user_name == 'ishibashi':
        current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        excel_filename = f'user_data_{current_time}.xlsx'
        st.download_button(label='管理者用pass', data=excel_data, file_name=excel_filename, key='download_data')

def display_image(i):
    img = Image.open(image_folder + f'{i}.png')
    return img    

def show_question(imgIndex):
    #st.empty()で画像を置く場所を先に確保し，その場所に黒画像orピクトグラムを表示している
    showImg = st.empty()
    # はじめは黒画像
    showImg.image(blackImg)
    # 追加: カウントダウンの表示
    countdown_text = st.empty()
    # 入力フォーム
    input_text = st.text_input(f'({imgIndex})は何に見えますか？')
    # 画像を表示
    img = display_image(imgIndex)
    showImg.image(img)
    #入力内容をデータベースへ保存
    if st.button(f'({imgIndex})の回答を送信'):
        #タイムスタンプを更新
        st.session_state.timestamps[f'{imgIndex}']['save'] = time.time()
        #回答にかかった時間を計算
        elapsed_time = st.session_state.timestamps[f'{imgIndex}']['save'] - st.session_state.timestamps[f'{imgIndex}']['start']
        #データベースへ保存
        c.execute(f'INSERT INTO {st.session_state.user_name}(image_number,input_text,time,timelimit) VALUES (?, ?, ?, ?)',
                  (imgIndex, input_text, elapsed_time, elapsed_time <= timelimit))
        conn.commit()

        if elapsed_time <= timelimit:
            st.success('送信完了です．次へ進んでください．')
        else:
            st.warning('制限時間切れです．次へ進んでください．')

        st.session_state.imgIndex += 1
        st.session_state.otherQ = False
        st.button('閉じる')
    #表示時間のカウントダウン
    while st.session_state.timestamps[f'{imgIndex}']['sleeptime'] > 0:
        st.session_state.timestamps[f'{imgIndex}']['sleeptime'] -= 0.1
        countdown_text.text(f'ピクトグラム表示 残り時間: {st.session_state.timestamps[f"{imgIndex}"]["sleeptime"]:.1f} 秒')
        time.sleep(0.1)
    showImg.image(blackImg)
    #解答時間のカウントダウン
    while st.session_state.timestamps[f'{imgIndex}']['countdown'] > 0:
        st.session_state.timestamps[f'{imgIndex}']['countdown'] -= 0.1
        countdown_text.text(f'回答 残り時間: {st.session_state.timestamps[f"{imgIndex}"]["countdown"]:.1f} 秒')
        time.sleep(0.1)
    
def page1():
    if st.session_state.access_check:
        st.divider()
        st.subheader('個人情報の回答にご協力ください')

        age = st.number_input('1.年齢を教えてください',value=20)
        sex = st.selectbox('2.性別を教えてください',('男','女','未回答'))
        job = st.text_input('3.ご職業を可能な範囲で教えてください（例：学生）')

        if st.button('入力内容を送信'):
            #データベースに個人情報を強引に記録
            c.execute(f'''
                    INSERT INTO {st.session_state.user_name}(image_number,input_text,time,timelimit) VALUES (?, ?, ?, ?)
            ''', (0, age, None, None))
            conn.commit()
            c.execute(f'''
                    INSERT INTO {st.session_state.user_name}(image_number,input_text,time,timelimit) VALUES (?, ?, ?, ?)
            ''', (0, sex, None, None))
            conn.commit()
            c.execute(f'''
                    INSERT INTO {st.session_state.user_name}(image_number,input_text,time,timelimit) VALUES (?, ?, ?, ?)
            ''', (0, job, None, None))
            conn.commit()
            # ボタンを押した後にページをリロードする
            st.session_state.page_id = 'page2'
            st.session_state.user_check = False
            #ボタンを押すとstreamlitの仕様で画面が更新される
            st.button('例題へ進む')
        # ユーザー情報を表示
        #st.table(data)

def page2():
    st.success(f'あなたのユーザー名は {st.session_state.user_name} です')
    st.subheader('例題')
    st.text('例題は何度も解くことができます．完了したら画面下部のボタンから本番へ進んでください．')
    st.info("""
            
            **回答のヒント**: 
            
            回答は分かる範囲でOKです．具体名まで合っていると正解としています．例題では「おにぎり」が正解ですが，「食べ物」の場合は一部正解として集計します．
            
            """)
    if st.button('例題を開始する'):
        st.session_state.example = True
    st.divider()
    if st.session_state.example:
        sleeptime = 5
        countdown = 25
        start_time = time.time() #開始時間
        showImg = st.empty()
        showImg.image(blackImg)
        countdown_text = st.empty()
        input_text = st.text_input('これは何に見えますか？')
        img = display_image(0) #0.pngを例題用の画像にする
        showImg.image(img)
        if st.button('回答を送信'):
            st.session_state.example = False
            finish_time = time.time()
            user_time = finish_time - start_time
            if user_time <= timelimit:
                st.success('送信完了です．閉じるを押し，本番を開始してください')
            else:
                st.warning('制限時間切れです．閉じるを押し，本番を開始してください')
            if st.button('閉じる'):
                # st.session_state.example = False
                st.experimental_rerun()
        while sleeptime > 0:
            sleeptime -= 0.1
            countdown_text.text(f'ピクトグラム表示 残り時間: {sleeptime:.1f} 秒')
            time.sleep(0.1)
        showImg.image(blackImg)
        while countdown > 0:
            countdown -= 0.1
            countdown_text.text(f'回答 残り時間: {countdown:.1f}秒')
            time.sleep(0.1)
    #ページ遷移ボタンの配置
    col1, col2, col3 = st.columns(3)
    with col1:
        button1 = st.button('前のページへ戻る')
    with col3:
        button4 = st.button('本番へ進む')
    if button1:
        st.session_state.page_id = 'page1'
        st.experimental_rerun()
    if button4:
        st.session_state.page_id = 'page3'
        st.experimental_rerun()

def page3():
    st.success(f'あなたのユーザー名は {st.session_state.user_name} です')
    st.subheader('本番')
    st.text('問題は全50問です．休憩はいつでも取ることができます．')
    #画像番号
    if 'imgIndex' not in st.session_state:
        st.session_state.imgIndex = 1
    #回答時間と制限時間
    if 'timestamps' not in st.session_state:
        st.session_state.timestamps = {f'{i+1}': {'start': None, 'save': None, 'sleeptime':sleeptime, 'countdown': countdown} for i in range(imgsum)}
    #連続して問題を出す用
    if 'otherQ' not in st.session_state:
        st.session_state.otherQ = False
    try:
        showImg = st.empty()
        if st.session_state.imgIndex == imgsum + 1:
            # 終了ボタンがクリックされた時にありがとうを表示
            if st.button('終了'):
                st.success('これで実験は終了です．ありがとうございました．')
        elif st.session_state.user_name is not None and st.session_state.imgIndex <= imgsum:
            if st.button(f'({st.session_state.imgIndex})を開始'):
                if st.session_state.otherQ == False : st.session_state.otherQ = True
                #表示ボタンがクリックされたときにタイムスタンプを更新
                st.session_state.timestamps[f'{st.session_state.imgIndex}']['start'] = time.time()
            if st.session_state.otherQ:
                show_question(st.session_state.imgIndex)
    finally:
        #データベースクローズ
        conn.close()

if st.session_state.page_id == 'page2':
    page2()
elif st.session_state.page_id == 'page3':
    page3()
else:
    page1()

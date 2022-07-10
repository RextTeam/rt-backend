# rt-backend
RTのバックエンドです。  

## 要件
* Python 3.10以上
* MySQL/MariaDB
* `requirements.txt`にあるPython用ライブラリ全て

## 用意
1. 要件にあるものをまずインストールします。
2. `data.template.toml`と`secret.template.toml`のコピーを作って、名前をそれぞれ`.template`を消した名前にします。
3. `data.toml`と`secret.toml`の中身をそこに書かれてる通りに適切なものを書き込みます。
4. リポジトリ`rt-lib`を`clone`してフォルダの名前を`rtlib`にする。
5. `rt-frontend`をクローンする。
5. ルートに`secret.key`を`rtlib/rtlib/common/make_key.py`で作る。もしバックエンド側にあるならそれをコピーする。

## 起動方法
`python3 main.py test`で起動が可能です。  
本番時は`test`を`production`に変えてください。
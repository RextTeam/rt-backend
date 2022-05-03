# rt-backend
RTのバックエンドです。  

## 要件
* Python 3.10以上
* MySQL/MariaDB
* `requirements.txt`にあるPython用ライブラリ全て

## 用意
1. 要件にあるものをまずインストールします。
2. `data.json.template`と`secret.json.template`のコピーを作って、名前をそれぞれ`.template`を消した名前にします。
3. `data.json`と`secret.json`の中身をそこに書かれてる通りに適切なものを書き込みます。
4. リポジトリ`rt-lib`を`clone`してフォルダの名前を`rtlib`にする。

## 起動方法
`python3 main.py test`で起動が可能です。  
本番時は`test`を`production`に変えてください。  
もし`canary`として起動する場合は、`test`引数に加えて`canary`を引数に入れてください。
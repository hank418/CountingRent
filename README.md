# CountingRent

## Installation
#### python3 虛擬機環境
```sh
$ apt-get install python3 python3-pip
$ pip3 install virtualenv
```
#### line-bot-sdk
```sh
$ virtualenv -p python3 <envName>
$ source <envName>/bin/activate
$ pip3 install line-bot-sdk
```
## Setup
```sh
$ vim secure.key
```
#### secure.key
> {
>    "Channel Access Token": "",
>    "Channel Secret": "",
>    "Database Path":"/path/of/database"
> }

## Usage
你可以用 'help' 印出本訊息
- 📌  '本月'
  - <本月 xx度>
    - 更新本月電度數
  - <本月>
    - 印出本月房租
- 📌  '更新'
  - <更新 本月 xx度>
  - <更新 上月 xx度>
  - <更新 x月 xx度>
    - 更新之前月份的度數


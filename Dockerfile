FROM archlinux:latest

RUN pacman --noconfirm -Syu

RUN pacman -S --noconfirm bcc bcc-tools python-bcc python-pip

RUN pip3 install prometheus-client==0.15.0 requests==2.28.1 pytest python-dotenv

WORKDIR /app

COPY . .

CMD ["python3", "caller.py"]

#! /bin/bash

if [[ "$EUID" -ne 0 ]]; then
    echo "Please re-run using sudo or as root"
    exit 1
fi

echi "Install requirements"
sudo apt install -y python3-pip pipenv

echo "Creating folders"
vmnotification_folders=( \
  "/opt/vmotionator"  \
  "/etc/vmotionator"  \
)
for item in ${vmnotification_folders[@]}; do
  echo " Creating folder '$item'"
  mkdir -p $item
done


echo "Copying files to '/opt/vmotionator'"
vmnotification_files=(          \
  "LICENSE"                     \
  "Pipfile"                     \
  "Pipfile.lock"                \
  "README.md"                   \
  "utils.py"                    \
  "vmotionator.py"           \
  "vmotionator_config.py"    \
  "vmotionator_exception.py" \
  "vmotionator_service.py"   \
)
for item in ${vmnotification_files[@]}; do
  echo " Copying file '$item'"
  cp $item /opt/vmotionator
done

echo "Setting file execute permission on '/opt/vmotionator/vmotionator.py'"
chmod a+x /opt/vmotionator/vmotionator.py

echo "Copying 'vmotionator' file to '/etc/default/'"
cp ./vmotionator /etc/default/

echo "Copying service configuration file to '/etc/vmotionator/'"
cp ./vmotionator.conf* /etc/vmotionator/

echo "Copying systemd service to '/etc/systemd/system'"
cp ./vmotionator.service /etc/systemd/system/

echo "Create pipenv in '/opt/vmotionator'"
pushd /opt/vmotionator
PIPENV_VENV_IN_PROJECT=1 pipenv install
popd

echo "Enabling and starting 'vmnotification.service'"
systemctl daemon-reload
systemctl enable vmotionator.service
systemctl restart vmotionator.service

echo ""
echo "MAKE SURE TO EDIT THE CONFIGURATION AND RESTART THE SERVICE!"
echo "'sudo vi /etc/vmotionator/vmotionator.conf; sudo systemctl restart vmotionator'"
echo ""
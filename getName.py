# import os

# root_ = 'sample'

# departList = []
# personList = []
# all_data = []

# for depart_ in os.listdir(root_):
#     departList.append(os.path.join(root_, depart_))

# for detact in departList:
#     for person_ in os.listdir(detact):
#         personList.append(os.path.join(detact, person_))

# for detact in personList:
#     for file_ in os.listdir(detact):
#         all_data.append(os.path.join(detact, file_))

import os

root_ = 'sample'

departList = []
personList = []
all_data = []

# Get a list of all department folders
for depart_ in os.listdir(root_):
    departList.append(os.path.join(root_, depart_))

# Get a list of all person folders within each department
for detact in departList:
    for person_ in os.listdir(detact):
        personList.append(os.path.join(detact, person_))

# Collect all files for each person and write them to a text file
for detact in personList:
    files = []
    for file_ in os.listdir(detact):
        files.append(os.path.join(detact, file_))
    
    # Create the output file path
    person_folder_name = os.path.basename(detact)
    department_folder_name = os.path.basename(os.path.dirname(detact))
    output_file_path = os.path.join(department_folder_name, f"{person_folder_name}_files.txt")
    
    # Ensure the department directory exists for output files
    os.makedirs(department_folder_name, exist_ok=True)
    
    # Write the list of files to the text file
    with open(output_file_path, 'w') as f:
        for file_path in files:
            f.write(file_path + '\n')

print("Files have been written to text files successfully.")

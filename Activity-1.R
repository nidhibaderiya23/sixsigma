library(gert)
library(credentials)

credentials::set_github_pat()   # paste your token in the popup

gert::git_config_global_set("user.name", "nidhibaderiya23")
gert::git_config_global_set("user.email", "nb679@cornell.edu")

gert::git_reset_mixed()          # unstage everything (your files are not changed)
gert::git_add("Activity-1.R")    # stage only Activity-1.R
gert::git_commit("my first commit")
gert::git_push()
gert::git_log(max = 3)


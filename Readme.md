# userChrome Loader
This is a template intended to make it easier for end-users to manually load and manage custom CSS.

## Setup Instructions
1. In your **chrome** folder, save the **userchrome-loader** folder from this repo.
   
2. If you already have custom CSS in your **userChrome.css** file, back it up by copying the contents to a new CSS file indside the **userchrome-loader** folder.
  
  - If you don't have any custom CSS in your userChrome.css file, skip this step.

3. Copy the **userChrome.css** file from this repo into your own userChrome.css file. 

  - This should be the only content in your userChrome.css file.

4. When you find a customization you want to add, copy the contents to a new CSS file inside the **userchrome-loader** folder. 

5. Add the **@import** rule to **loader.css** with the path to the new CSS file made in the last step. 

*Examples:*

@import "userchrome-loader/example.css";

@import "userchrome-loader/new-folder/example2.css";

## Why Use uCL?

Orginizing custom CSS into their own files and folders will significantly aid users in customization and file management, as well as troubleshooting bugs by enabling easier isolation of custom CSS through @import rules. 

This also allows Mod creaters to make their customizations more modular, allowing end users to pick and choose which features they want to add. 

## Mod Creators / CSS Wizards:
Now when you upload some CSS with the intention of sharing, you can orginize your project folder structure by feauture. See [Natsumi Browser](https://github.com/greeeen-dev/natsumi-browser/tree/main) for the ideal project structure.

## Further Examples:

Here's what your **chrome** folder should look like:

![image](https://github.com/user-attachments/assets/80a1ef97-1afb-44aa-9ca8-d87ed70df9eb)

Here's what your **userchrome-loader** folder should look like, with some example Mods already in place:

![image](https://github.com/user-attachments/assets/384615b3-0fc4-40d3-ac0b-d6692a371f4b)

And here's an example of **loader.css**

```
/* === Load custom files === */

@import "userchrome-loader/Cohesion/Cohesion.css";
@import "userchrome-loadernatsumi/config.css";
@import "userchrome-loadernatsumi/preload.css";
@import "userchrome-loadernatsumi/patches.css";
@import "userchrome-loadernatsumi/base-ui.css";
@import "userchrome-loadernatsumi/tab-groups.css";
@import "userchrome-loadernatsumi/horizontal-tabs.css";
@import "userchrome-loadernatsumi/natsumi-urlbar.css";
@import "userchrome-loadernatsumi/natsumi-loading.css";
@import "userchrome-loadernatsumi/ui-tweaks.css";
```



document.addEventListener("DOMContentLoaded", () => {
    // Tab switching functionality
    const tabs = document.querySelectorAll(".settings-tab")
    const tabContents = document.querySelectorAll(".settings-tab-content")
  
    tabs.forEach((tab) => {
      tab.addEventListener("click", function () {
        // Remove active class from all tabs and contents
        tabs.forEach((t) => t.classList.remove("active"))
        tabContents.forEach((c) => c.classList.remove("active"))
  
        // Add active class to clicked tab and corresponding content
        this.classList.add("active")
        const tabId = this.getAttribute("data-tab")
        document.getElementById(tabId).classList.add("active")
      })
    })
  
    // Delete account modal functionality
    const deleteAccountBtn = document.getElementById("deleteAccountBtn")
    const deleteAccountModal = document.getElementById("deleteAccountModal")
    const modalCloseBtns = document.querySelectorAll(".modal-close")
  
    if (deleteAccountBtn && deleteAccountModal) {
      deleteAccountBtn.addEventListener("click", () => {
        deleteAccountModal.classList.add("active")
      })
    }
  
    modalCloseBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        deleteAccountModal.classList.remove("active")
      })
    })
  
    // Close modal when clicking outside
    window.addEventListener("click", (e) => {
      if (e.target === deleteAccountModal) {
        deleteAccountModal.classList.remove("active")
      }
    })
  
    // Password strength indicator
    const newPassword1 = document.getElementById("new_password1")
    if (newPassword1) {
      newPassword1.addEventListener("input", function () {
        const password = this.value
        const passwordHints = document.querySelector(".password-hints")
  
        if (passwordHints) {
          const hints = passwordHints.querySelectorAll("li")
  
          // Check for at least 8 characters
          if (password.length >= 8) {
            hints[0].classList.add("valid")
          } else {
            hints[0].classList.remove("valid")
          }
  
          // Check for at least one uppercase letter
          if (/[A-Z]/.test(password)) {
            hints[1].classList.add("valid")
          } else {
            hints[1].classList.remove("valid")
          }
  
          // Check for at least one number
          if (/[0-9]/.test(password)) {
            hints[2].classList.add("valid")
          } else {
            hints[2].classList.remove("valid")
          }
  
          // Check for at least one special character
          if (/[^A-Za-z0-9]/.test(password)) {
            hints[3].classList.add("valid")
          } else {
            hints[3].classList.remove("valid")
          }
        }
      })
    }
  
    // Confirm password match validation
    const newPassword2 = document.getElementById("new_password2")
    if (newPassword1 && newPassword2) {
      newPassword2.addEventListener("input", () => {
        if (newPassword1.value !== newPassword2.value) {
          newPassword2.setCustomValidity("Passwords don't match")
        } else {
          newPassword2.setCustomValidity("")
        }
      })
    }
  
    // Auto-fill email in delete account modal
    const deleteAccountForm = document.getElementById("deleteAccountForm")
    if (deleteAccountForm) {
      const userEmail = document
        .querySelector(".email-badge")
        ?.textContent.trim()
        .replace(/^[^:]+: /, "")
      if (userEmail) {
        const confirmEmailInput = document.getElementById("confirmEmail")
        if (confirmEmailInput) {
          confirmEmailInput.value = userEmail
        }
      }
    }
  
    // Fade out messages after 5 seconds
    const messages = document.querySelectorAll(".alert")
    if (messages.length > 0) {
      setTimeout(() => {
        messages.forEach((message) => {
          message.style.opacity = "0"
          message.style.transition = "opacity 1s"
          setTimeout(() => {
            message.style.display = "none"
          }, 1000)
        })
      }, 5000)
    }
  })
  
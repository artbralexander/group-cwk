import { ref } from "vue"
import { subscribeToNotifications } from "../services/notifications"

let categoriesUnsubscribe = null
export function useCategories(groupIdRef){
    const categories = ref([])
    const loadingCategories = ref(false)
    const categoriesError = ref("")
    async function fetchCategories(){
        if (!groupIdRef.value){
            return
        }
        loadingCategories.value = true
        categoriesError.value = ""

        try{
            const response = await fetch(`/api/groups/${groupIdRef.value}/categories`,{credentials:"include"})
            if (!response.ok){
                const body = await response.json().catch(() => ({}))
                throw new Error(body.detail || "Failed to fetch categories")
            }

            categories.value = await response.json()
        }
        catch (err){
            categoriesError.value = err.message || "failed to fetch categories"
        }
        finally{
            loadingCategories.value = false
        }
    }

    async function updateCategory(categoryID, payload){
        const response = await fetch(`/api/groups/${groupIdRef.value}/categories/${categoryID}`,
            {
                method:"PUT",
                headers: {"Content-Type":"application/json"},
                credentials: "include",
                body: JSON.stringify(payload)
            }
        )
        if (!response.ok){
            const body = await response.json()
            throw new Error(body.detail || "Failed to update category")
        }
        return await response.json()
    }

    async function deleteCategory(categoryID){
        const res = await fetch(
            `/api/groups/${groupIdRef.value}/categories/${categoryID}`,
            {
                method:"DELETE",
                credentials:"include"
            }
        )
        if (!res.ok){
            const body = await res.json().catch(() => ({}))
            throw new Error(body.detail || "Failed to delete category")
        }
    }

    async function createCategory(payload){
        if (!groupIdRef.value){
            return
        }
        const response = await fetch(`/api/groups/${groupIdRef.value}/categories`,
            {
                method:"POST",
                headers:{"Content-Type":"application/json"},
                credentials:"include",
                body:JSON.stringify(payload)
            }
        )
        if (!response.ok){
            const body = await response.json().catch(() => ({}))
            throw new Error(body.detail || "Failed to create category")
        }
        return response.json()
    }

    return{
        categories,
        loadingCategories,
        categoriesError,
        fetchCategories,
        createCategory,
        updateCategory,
        deleteCategory,
        connectToCategoryNotifications(onChange){
            if (categoriesUnsubscribe || typeof window === "undefined"){
                return
            }
            categoriesUnsubscribe = subscribeToNotifications("categories_changed", (data) => {
                if (data?.group_id && typeof onChange === "function"){
                    onChange(data.group_id, data)
                }
            })
        }
    }
}

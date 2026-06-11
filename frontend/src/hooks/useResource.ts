import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/api/client'

export interface ListParams {
  page?: number
  pageSize?: number
  search?: string
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
  filters?: Record<string, string | number | boolean>
}

export interface ListResult<T> {
  data: T[]
  total: number
  page: number
  pageSize: number
}

interface BackendListResponse<T> {
  items: T[]
  total: number
}

async function fetchList<T>(endpoint: string, params: ListParams): Promise<ListResult<T>> {
  const { page = 1, pageSize = 20, search, sortBy, sortOrder = 'asc', filters } = params
  const skip = (page - 1) * pageSize

  const { data } = await apiClient.get<BackendListResponse<T>>(`${endpoint}/`, {
    params: {
      skip,
      limit: pageSize,
      ...(search ? { q: search } : {}),
      ...(sortBy ? { sort_by: sortBy } : {}),
      sort_dir: sortOrder,
      ...filters,
    },
  })

  return { data: data.items, total: data.total, page, pageSize }
}

async function fetchOne<T>(endpoint: string, id: string | number): Promise<T> {
  const { data } = await apiClient.get<T>(`${endpoint}/${id}`)
  return data
}

async function createOne<T>(endpoint: string, payload: unknown): Promise<T> {
  const { data } = await apiClient.post<T>(`${endpoint}/`, payload)
  return data
}

async function updateOne<T>(endpoint: string, id: string | number, payload: unknown): Promise<T> {
  const { data } = await apiClient.put<T>(`${endpoint}/${id}`, payload)
  return data
}

async function removeOne(endpoint: string, id: string | number): Promise<void> {
  await apiClient.delete(`${endpoint}/${id}`)
}

export function useResource<T extends Record<string, unknown>>(
  endpoint: string,
  options: {
    listParams?: ListParams
    id?: string | number
  } = {},
) {
  const queryClient = useQueryClient()
  const { listParams, id } = options

  const list = useQuery({
    queryKey: [endpoint, 'list', listParams],
    queryFn: () => fetchList<T>(endpoint, listParams!),
    enabled: listParams !== undefined,
  })

  const detail = useQuery({
    queryKey: [endpoint, 'detail', id],
    queryFn: () => fetchOne<T>(endpoint, id!),
    enabled: id !== undefined,
  })

  const create = useMutation<T, Error, unknown>({
    mutationFn: (payload) => createOne<T>(endpoint, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [endpoint, 'list'] })
    },
  })

  const update = useMutation<T, Error, { id: string | number; payload: unknown }>({
    mutationFn: ({ id, payload }) => updateOne<T>(endpoint, id, payload),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: [endpoint, 'list'] })
      queryClient.invalidateQueries({ queryKey: [endpoint, 'detail', id] })
    },
  })

  const remove = useMutation<void, Error, string | number>({
    mutationFn: (id) => removeOne(endpoint, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [endpoint, 'list'] })
    },
  })

  return { list, detail, create, update, remove }
}

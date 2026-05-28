import { Route, Routes } from "react-router-dom"

import { AppShell } from "@/components/layout/AppShell"
import CreatePage from "@/pages/CreatePage"
import EditPage from "@/pages/EditPage"
import HistoryPage from "@/pages/HistoryPage"
import ListPage from "@/pages/ListPage"
import ResultsPage from "@/pages/ResultsPage"
import StudentPage from "@/pages/StudentPage"
import TeacherPage from "@/pages/TeacherPage"

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/" element={<ListPage />} />
        <Route path="/create" element={<CreatePage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/edit/:id" element={<EditPage />} />
        <Route path="/student/:id" element={<StudentPage />} />
        <Route path="/results/:id" element={<ResultsPage />} />
        <Route path="/teacher/:id" element={<TeacherPage />} />
      </Route>
    </Routes>
  )
}

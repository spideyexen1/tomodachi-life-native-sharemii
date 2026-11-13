/* SPDX-License-Identifier: GPL-3.0-only
 * Small owning buffers for the runtime's C++14/no-exceptions build. They avoid
 * a dependency on MSVC STL headers newer than the pinned Clang compiler.
 * Placement construction and allocation use the existing Dear ImGui helpers. */
template<class C> class SmText {
    C *p; size_t n, capacity;
    static size_t length(const C *s) { size_t z = 0; if (s) while (s[z]) ++z; return z; }
    void assign(const C *s, size_t count) {
        C *copy = (C *)IM_ALLOC((count + 1) * sizeof(C)); IM_ASSERT(copy);
        if (count) memcpy(copy, s, count * sizeof(C)); copy[count] = 0;
        IM_FREE(p); p = copy; n = count; capacity = count;
    }
public:
    static const size_t npos = (size_t)-1;
    SmText() : p(NULL), n(0), capacity(0) { assign(NULL, 0); }
    SmText(const C *s) : p(NULL), n(0), capacity(0) { assign(s, length(s)); }
    SmText(const C *s, size_t count) : p(NULL), n(0), capacity(0) { assign(s, count); }
    SmText(size_t count, C fill) : p(NULL), n(0), capacity(0) {
        p = (C *)IM_ALLOC((count + 1) * sizeof(C)); IM_ASSERT(p);
        n = capacity = count; for (size_t i = 0; i < count; ++i) p[i] = fill; p[n] = 0;
    }
    SmText(const SmText& s) : p(NULL), n(0), capacity(0) { assign(s.p, s.n); }
    ~SmText() { IM_FREE(p); }
    SmText& operator=(const SmText& s) { if (this != &s) assign(s.p, s.n); return *this; }
    SmText& operator+=(const SmText& s) {
        size_t old = n, count = s.n, total = n + count;
        if (total > capacity) {
            size_t next = capacity ? capacity * 2 : 16; if (next < total) next = total;
            C *copy = (C *)IM_ALLOC((next + 1) * sizeof(C)); IM_ASSERT(copy);
            if (old) memcpy(copy, p, old * sizeof(C)); copy[old] = 0;
            IM_FREE(p); p = copy; capacity = next;
        }
        if (count) memmove(p + old, s.p, count * sizeof(C));
        n = total; p[n] = 0; return *this;
    }
    SmText& operator+=(C c) { C pair[2] = {c, 0}; return *this += SmText(pair, 1); }
    friend SmText operator+(SmText a, const SmText& b) { a += b; return a; }
    const C *c_str() const { return p; }
    C *data() { return p; } const C *data() const { return p; }
    size_t size() const { return n; } bool empty() const { return !n; }
    C& operator[](size_t i) { return p[i]; } const C& operator[](size_t i) const { return p[i]; }
    C *begin() { return p; } C *end() { return p + n; }
    const C *begin() const { return p; } const C *end() const { return p + n; }
    SmText substr(size_t start, size_t count = npos) const {
        if (start > n) start = n; if (count > n - start) count = n - start;
        return SmText(p + start, count);
    }
    size_t find_last_of(const C *choices) const {
        for (size_t i = n; i; --i) for (const C *c = choices; *c; ++c) if (p[i - 1] == *c) return i - 1;
        return npos;
    }
};
typedef SmText<char> SmString;
typedef SmText<wchar_t> SmWString;
static SmString sm_number(size_t value) { char b[40]; snprintf(b, sizeof b, "%zu", value); return b; }

template<class T> class SmVector {
    T *p; size_t n, capacity;
    void reserve(size_t count) {
        if (count <= capacity) return;
        size_t next = capacity ? capacity * 2 : 8; if (next < count) next = count;
        T *fresh = (T *)IM_ALLOC(next * sizeof(T)); IM_ASSERT(fresh);
        for (size_t i = 0; i < next; ++i) IM_PLACEMENT_NEW(fresh + i) T();
        for (size_t i = 0; i < n; ++i) fresh[i] = p[i];
        for (size_t i = 0; i < capacity; ++i) p[i].~T();
        IM_FREE(p); p = fresh; capacity = next;
    }
public:
    SmVector() : p(NULL), n(0), capacity(0) {}
    explicit SmVector(size_t count) : p(NULL), n(0), capacity(0) { resize(count); }
    SmVector(size_t count, const T& value) : p(NULL), n(0), capacity(0) { resize(count); for (size_t i = 0; i < n; ++i) p[i] = value; }
    SmVector(const SmVector&) = delete; SmVector& operator=(const SmVector&) = delete;
    ~SmVector() { for (size_t i = 0; i < capacity; ++i) p[i].~T(); IM_FREE(p); }
    size_t size() const { return n; } bool empty() const { return !n; }
    T *data() { return p; } const T *data() const { return p; }
    T *begin() { return p; } T *end() { return n ? p + n : p; }
    const T *begin() const { return p; } const T *end() const { return n ? p + n : p; }
    T& operator[](size_t i) { return p[i]; } const T& operator[](size_t i) const { return p[i]; }
    void resize(size_t count) { reserve(count); for (size_t i = n; i < count; ++i) p[i] = T(); n = count; }
    void clear() { for (size_t i = 0; i < n; ++i) p[i] = T(); n = 0; }
    void push_back(const T& value) { T copy(value); reserve(n + 1); p[n++] = copy; }
    void erase(T *at) { size_t index = (size_t)(at - p); for (size_t i = index + 1; i < n; ++i) p[i - 1] = p[i]; p[--n] = T(); }
    void insert(T *at, const T *first, const T *last) { IM_ASSERT(at == end()); for (; first != last; ++first) push_back(*first); }
    void swap(SmVector& other) {
        T *q = p; p = other.p; other.p = q;
        size_t z = n; n = other.n; other.n = z; z = capacity; capacity = other.capacity; other.capacity = z;
    }
};
